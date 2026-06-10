"""BM25 lexical scoring with bm25s preferred and rank-bm25 fallback."""

from __future__ import annotations

import concurrent.futures
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


def _tokenize_all(texts: list[str]) -> list[list[str]]:
    if len(texts) < 4000:
        return [tokenize(t) for t in texts]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        return list(executor.map(tokenize, texts, chunksize=2000))


def _rank_bm25_scores(texts: list[str], query: str) -> np.ndarray:
    from rank_bm25 import BM25Okapi

    tokenized = _tokenize_all(texts)
    bm25 = BM25Okapi(tokenized)
    return np.asarray(bm25.get_scores(tokenize(query)), dtype=np.float32)


def _bm25s_scores(texts: list[str], query: str) -> np.ndarray:
    import bm25s

    tokenized = _tokenize_all(texts)
    retriever = bm25s.BM25()
    retriever.index(tokenized, show_progress=False)
    query_tokens = tokenize(query)
    if hasattr(retriever, "get_scores"):
        return np.asarray(retriever.get_scores(query_tokens), dtype=np.float32)

    raise AttributeError("bm25s backend lacks get_scores(); use rank_bm25 fallback.")


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

    texts = []
    for c in candidates:
        t = candidate_text(c)
        c["_cached_text"] = t  # Cache for reuse by compute_features
        texts.append(t)
    scores, used_backend = bm25_scores(texts, query=query, backend=backend)
    if pool_size > 0 and pool_size < len(scores):
        idx = np.argpartition(-scores, pool_size - 1)[:pool_size]
    else:
        idx = np.arange(len(scores))
    return normalize_scores({int(i): float(scores[i]) for i in idx}), used_backend
