"""BM25 lexical scoring with bm25s preferred and rank-bm25 fallback."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np

from redrob_ranker.constants import JD_QUERY
from redrob_ranker.text import candidate_text, tokenize

Bm25Backend = Literal["auto", "bm25s", "rank_bm25"]


def normalize_scores(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo = min(vals)
    hi = max(vals)
    if math.isclose(lo, hi):
        return {k: 0.0 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def _rank_bm25_scores(texts: list[str], query: str) -> np.ndarray:
    from rank_bm25 import BM25Okapi

    tokenized = [tokenize(t) for t in texts]
    bm25 = BM25Okapi(tokenized)
    return np.asarray(bm25.get_scores(tokenize(query)), dtype=np.float32)


def _bm25s_scores(texts: list[str], query: str) -> np.ndarray:
    import bm25s

    tokenized = [tokenize(t) for t in texts]
    retriever = bm25s.BM25()
    retriever.index(tokenized, show_progress=False)
    query_tokens = tokenize(query)
    if hasattr(retriever, "get_scores"):
        return np.asarray(retriever.get_scores(query_tokens), dtype=np.float32)

    results, scores = retriever.retrieve([query_tokens], k=len(texts), show_progress=False)
    flat_results = np.asarray(results[0])
    flat_scores = np.asarray(scores[0], dtype=np.float32)
    ordered_scores = np.zeros(len(texts), dtype=np.float32)

    # Depending on bm25s version, results may be integer IDs or corpus objects.
    for rank, doc_ref in enumerate(flat_results):
        try:
            idx = int(doc_ref)
        except (TypeError, ValueError):
            idx = rank
        if 0 <= idx < len(texts):
            ordered_scores[idx] = flat_scores[rank]
    return ordered_scores


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
    candidates: list[dict], pool_size: int = 0, backend: Bm25Backend = "auto"
) -> tuple[dict[int, float], str]:
    """Return normalized BM25 scores and backend name.

    `pool_size <= 0` scores every candidate. That is the official challenge path.
    """

    if not candidates:
        return {}, "none"

    texts = [candidate_text(c) for c in candidates]
    scores, used_backend = bm25_scores(texts, backend=backend)
    if pool_size > 0 and pool_size < len(scores):
        idx = np.argpartition(-scores, pool_size - 1)[:pool_size]
    else:
        idx = np.arange(len(scores))
    return normalize_scores({int(i): float(scores[i]) for i in idx}), used_backend
