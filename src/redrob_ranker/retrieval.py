"""BM25 lexical scoring with bm25s preferred and rank-bm25 fallback."""

from __future__ import annotations

import concurrent.futures
import math
import multiprocessing
import os
from typing import Literal

import numpy as np

from redrob_ranker.constants import JD_QUERY
from redrob_ranker.text import (
    LOWERED_IMPORTANT_PHRASES,
    STOPWORDS,
    TOKEN_RE,
    candidate_text,
    tokenize,
)

# Import the shared cgroup helper. The underscore alias keeps existing test
# monkeypatches working without changes:
#   monkeypatch.setattr(retrieval_mod, "_cgroup_cpu_quota_count", lambda: 2)
from redrob_ranker._cgroup import cgroup_cpu_quota_count as _cgroup_cpu_quota_count

Bm25Backend = Literal["auto", "bm25s", "rank_bm25"]
_TOKENIZE_WORKER_CAP = 8
_PARALLEL_MIN_POOL = 4000
_QUERY_TEXTS: list[str] | None = None
_QUERY_TOKEN_INDEX: dict[str, int] = {}
_RENDER_CANDIDATES: list[dict] | None = None


def _resolve_tokenize_workers() -> int:
    host_cpus = os.cpu_count() or 1
    available = min(host_cpus, _cgroup_cpu_quota_count() or host_cpus)
    return max(1, min(_TOKENIZE_WORKER_CAP, available))


def normalize_scores(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo = min(vals)
    hi = max(vals)
    if math.isclose(lo, hi):
        return {k: 0.0 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def _tokenize_all(texts: list[str]) -> list[list[str]]:
    if len(texts) < _PARALLEL_MIN_POOL:
        return [tokenize(t) for t in texts]
    # Cap workers (audit-v2 hardening): an uncapped pool would spawn one process
    # per core on a many-core box for plain tokenization. Output is order-stable
    # and byte-identical regardless of worker count; this only bounds resource use.
    workers = _resolve_tokenize_workers()
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(tokenize, texts, chunksize=2000))


def _rank_bm25_scores(texts: list[str], query: str) -> np.ndarray:
    from rank_bm25 import BM25Okapi

    tokenized = _tokenize_all(texts)
    bm25 = BM25Okapi(tokenized)
    return np.asarray(bm25.get_scores(tokenize(query)), dtype=np.float32)


def _init_query_worker(query_token_index: dict[str, int]) -> None:
    global _QUERY_TOKEN_INDEX
    _QUERY_TOKEN_INDEX = query_token_index


def _candidate_text_for_index(index: int) -> str:
    if _RENDER_CANDIDATES is None:  # pragma: no cover - defensive worker guard
        raise RuntimeError("render worker candidate corpus was not initialized")
    return candidate_text(_RENDER_CANDIDATES[index])


def _candidate_text_all(candidates: list[dict]) -> list[str]:
    """Render retrieval text, using fork workers for large Docker pools."""

    global _RENDER_CANDIDATES
    if len(candidates) < _PARALLEL_MIN_POOL or os.name != "posix":
        return [candidate_text(candidate) for candidate in candidates]

    workers = _resolve_tokenize_workers()
    previous = _RENDER_CANDIDATES
    _RENDER_CANDIDATES = candidates
    try:
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=workers,
            mp_context=multiprocessing.get_context("fork"),
        ) as executor:
            return list(
                executor.map(
                    _candidate_text_for_index,
                    range(len(candidates)),
                    chunksize=1000,
                )
            )
    finally:
        _RENDER_CANDIDATES = previous


def _query_term_stats(text: str) -> tuple[int, tuple[int, ...]]:
    """Return exact tokenizer length and term frequencies for query terms only.

    BM25 needs the full document length, but a single-query run only needs term
    frequencies for tokens present in that query. Avoiding a materialized token
    list and a corpus-wide vocabulary is the main full-pool speedup.
    """

    lowered = text if text.islower() else text.lower()
    counts = [0] * len(_QUERY_TOKEN_INDEX)
    document_length = 0
    for match in TOKEN_RE.finditer(lowered):
        token = match.group(0)
        if token in STOPWORDS:
            continue
        document_length += 1
        column = _QUERY_TOKEN_INDEX.get(token)
        if column is not None:
            counts[column] += 1

    # ``tokenize`` appends one marker for every configured phrase found in the
    # document. Mirror that behavior exactly so lengths and query TFs are
    # byte-equivalent to bm25s' former full-index path.
    for phrase in LOWERED_IMPORTANT_PHRASES:
        if phrase in lowered:
            document_length += 1
            token = phrase.replace("/", "_").replace(" ", "_")
            column = _QUERY_TOKEN_INDEX.get(token)
            if column is not None:
                counts[column] += 1
    return document_length, tuple(counts)


def _query_term_stats_for_index(index: int) -> tuple[int, tuple[int, ...]]:
    if _QUERY_TEXTS is None:  # pragma: no cover - defensive worker guard
        raise RuntimeError("query worker text corpus was not initialized")
    return _query_term_stats(_QUERY_TEXTS[index])


def _query_stats_all(
    texts: list[str], query_token_index: dict[str, int]
) -> list[tuple[int, tuple[int, ...]]]:
    global _QUERY_TEXTS, _QUERY_TOKEN_INDEX
    if len(texts) < _PARALLEL_MIN_POOL:
        previous = _QUERY_TOKEN_INDEX
        _QUERY_TOKEN_INDEX = query_token_index
        try:
            return [_query_term_stats(text) for text in texts]
        finally:
            _QUERY_TOKEN_INDEX = previous

    workers = _resolve_tokenize_workers()
    if os.name == "posix":
        # The pinned Docker image uses Python 3.11's fork start method. Workers
        # inherit this read-only list, so only integer indices cross the process
        # pipe instead of ~500 MB of resume text.
        previous_texts = _QUERY_TEXTS
        previous_index = _QUERY_TOKEN_INDEX
        _QUERY_TEXTS = texts
        _QUERY_TOKEN_INDEX = query_token_index
        try:
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                initializer=_init_query_worker,
                initargs=(query_token_index,),
                mp_context=multiprocessing.get_context("fork"),
            ) as executor:
                return list(
                    executor.map(
                        _query_term_stats_for_index,
                        range(len(texts)),
                        chunksize=2000,
                    )
                )
        finally:
            _QUERY_TEXTS = previous_texts
            _QUERY_TOKEN_INDEX = previous_index

    # Windows uses spawn, so parent globals are not inherited. Sending each
    # text once matches the old cross-platform behavior while still returning
    # only compact query statistics instead of full token lists.
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_query_worker,
        initargs=(query_token_index,),
    ) as executor:
        return list(executor.map(_query_term_stats, texts, chunksize=2000))


def _bm25s_scores(texts: list[str], query: str) -> np.ndarray:
    query_tokens = tokenize(query)
    if not texts or not query_tokens:
        return np.zeros(len(texts), dtype=np.float32)

    unique_query_tokens = tuple(dict.fromkeys(query_tokens))
    query_token_index = {
        token: index for index, token in enumerate(unique_query_tokens)
    }
    stats = _query_stats_all(texts, query_token_index)
    document_lengths = np.fromiter(
        (length for length, _ in stats), dtype=np.int32, count=len(stats)
    )
    term_frequencies = np.asarray(
        [frequencies for _, frequencies in stats], dtype=np.float32
    )

    document_count = len(texts)
    average_length = document_lengths.mean()
    document_frequencies = np.count_nonzero(term_frequencies, axis=0)
    idf = np.asarray(
        [
            math.log(
                1.0
                + (document_count - int(frequency) + 0.5)
                / (int(frequency) + 0.5)
            )
            if frequency
            else 0.0
            for frequency in document_frequencies
        ],
        dtype=np.float32,
    )

    # bm25s 0.3.9 defaults: Lucene IDF, k1=1.5, b=0.75, float32
    # storage and float32 query accumulation. The casts below deliberately
    # reproduce those semantics exactly; regression tests compare every bit.
    length_normalizer = 1.5 * (
        (1.0 - 0.75) + 0.75 * document_lengths / average_length
    )
    scores = np.zeros(document_count, dtype=np.float32)
    for token in query_tokens:
        column = query_token_index[token]
        tf = term_frequencies[:, column]
        tf_component = tf / (length_normalizer + tf)
        scores += np.asarray(idf[column] * tf_component, dtype=np.float32)
    return scores


def bm25_scores(
    texts: list[str], query: str = JD_QUERY, backend: Bm25Backend = "auto"
) -> tuple[np.ndarray, str]:
    """Return scores and the backend actually used."""

    if backend in {"auto", "bm25s"}:
        try:
            return _bm25s_scores(texts, query), "bm25s"
        except Exception:
            if backend == "bm25s":
                raise
    try:
        return _rank_bm25_scores(texts, query), "rank_bm25"
    except ImportError as exc:
        raise RuntimeError(
            "No BM25 backend available. Install bm25s or rank-bm25 from requirements.txt."
        ) from exc


def retrieve_pool(
    candidates: list[dict],
    pool_size: int = 0,
    backend: Bm25Backend = "auto",
    query: str = JD_QUERY,
) -> tuple[dict[int, float], str]:
    """Return normalized BM25 scores and backend name.

    `pool_size <= 0` scores every candidate. That is the official challenge path.
    `query` defaults to the bundled JD; rank.py --jd supplies a compiled one.
    """

    if not candidates:
        return {}, "none"

    texts = _candidate_text_all(candidates)
    for candidate, text in zip(candidates, texts):
        candidate["_cached_text"] = text  # Cache for reuse by compute_features
    scores, used_backend = bm25_scores(texts, query=query, backend=backend)
    if pool_size > 0 and pool_size < len(scores):
        idx = np.argpartition(-scores, pool_size - 1)[:pool_size]
    else:
        idx = np.arange(len(scores))
    return normalize_scores({int(i): float(scores[i]) for i in idx}), used_backend
