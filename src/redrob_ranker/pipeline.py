"""End-to-end ranking pipeline."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from redrob_ranker.calibration import applies_to, apply_calibration
from redrob_ranker.features import compute_features, final_score
from redrob_ranker.io import iter_candidates, write_submission
from redrob_ranker.reasoning import build_reason
from redrob_ranker.retrieval import Bm25Backend, retrieve_pool
from redrob_ranker.validation import validate_rows

# Below this pool size, process-pool startup/IPC overhead outweighs the win, so we
# stay serial. This also keeps the demo API/Gradio paths (small uploads) single-process.
_PARALLEL_MIN_POOL = 4000
_PARALLEL_WORKER_CAP = 8


def _submission_score(raw_score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    return max(0.0, min(raw_score / max_score, 1.0))


# Per-worker compiled JD (None = bundled challenge JD). Set once per worker
# process via the pool initializer so it is pickled once, not per candidate.
_WORKER_JD = None


def _init_worker(jd) -> None:
    global _WORKER_JD
    _WORKER_JD = jd


def _score_one(args: tuple[dict, float, float | None]) -> tuple[object, float]:
    """Top-level (picklable) worker: features + final score for one candidate.

    Deterministic and side-effect free, so running it in a process pool yields
    output identical to the serial path (verified byte-for-byte on the 100K pool).
    """
    candidate, retrieval_score, semantic_score = args
    features = compute_features(candidate, config=_WORKER_JD)
    score = final_score(features, retrieval_score, semantic_score)
    features.total = score
    return features, score


@dataclass(slots=True)
class RankerConfig:
    top_k: int = 100
    candidate_pool_size: int = 0
    max_candidates: int | None = None
    bm25_backend: Bm25Backend = "auto"
    # 0 = auto (use up to _PARALLEL_WORKER_CAP cores for large pools); 1 = force serial.
    workers: int = 0
    # EXPERIMENTAL (default OFF): blend a model2vec/potion dense-retrieval feature.
    use_embeddings: bool = False
    embed_model: str = "minishlab/potion-retrieval-32M"
    # Optional compiled JD (rank.py --jd). None = bundled challenge JD; the
    # None path is byte-identical to the historical pipeline.
    jd: object | None = None


@dataclass(slots=True)
class RankingResult:
    rows: list[dict]
    loaded_count: int
    ranked_pool_count: int
    bm25_backend: str
    honeypots_detected: int
    honeypots_in_output: int
    raw_ranked: list[tuple[dict, object, float]] | None = None


def _resolve_workers(requested: int, pool_count: int) -> int:
    """Return the worker count to use (1 == serial)."""
    if requested == 1 or pool_count < _PARALLEL_MIN_POOL:
        return 1
    available = os.cpu_count() or 1
    if requested > 1:
        return max(1, min(requested, available))
    return max(1, min(_PARALLEL_WORKER_CAP, available))


def rank_candidates(candidates: list[dict], config: RankerConfig) -> tuple[list[tuple[dict, object, float]], str]:
    if config.jd is not None:
        retrieval_scores, used_backend = retrieve_pool(
            candidates, config.candidate_pool_size, backend=config.bm25_backend,
            query=config.jd.jd_query,
        )
    else:
        retrieval_scores, used_backend = retrieve_pool(
            candidates, config.candidate_pool_size, backend=config.bm25_backend
        )
    indices = (
        list(retrieval_scores.keys())
        if config.candidate_pool_size > 0
        else range(len(candidates))
    )

    semantic_scores: dict[int, float] = {}
    if config.use_embeddings:
        from redrob_ranker.constants import JD_QUERY
        from redrob_ranker.embeddings import StaticModelEmbedder, semantic_scores as _sem
        from redrob_ranker.text import candidate_text
        texts = [candidates[idx].get("_cached_text") or candidate_text(candidates[idx]) for idx in indices]
        local = _sem(texts, JD_QUERY, StaticModelEmbedder(config.embed_model))
        semantic_scores = {idx: local[pos] for pos, idx in enumerate(indices)}

    work = [
        (
            candidates[idx],
            retrieval_scores.get(idx, 0.0),
            semantic_scores.get(idx) if config.use_embeddings else None,
        )
        for idx in indices
    ]

    workers = _resolve_workers(config.workers, len(work))
    ranked: list[tuple[dict, object, float]] = []
    if workers == 1:
        global _WORKER_JD
        prev_jd = _WORKER_JD
        _WORKER_JD = config.jd
        try:
            for item in work:
                features, score = _score_one(item)
                ranked.append((item[0], features, score))
        finally:
            _WORKER_JD = prev_jd
    else:
        chunksize = max(1, len(work) // (workers * 8))
        with ProcessPoolExecutor(
            max_workers=workers, initializer=_init_worker, initargs=(config.jd,)
        ) as executor:
            results = executor.map(_score_one, work, chunksize=chunksize)
            for item, (features, score) in zip(work, results):
                ranked.append((item[0], features, score))

    ranked.sort(key=lambda item: (-item[2], item[0]["candidate_id"]))
    return ranked, used_backend


def rows_from_ranked(ranked: list[tuple[dict, object, float]], top_k: int) -> list[dict]:
    rows: list[dict] = []
    selected = ranked[:top_k]
    max_score = selected[0][2] if selected else 0.0
    for rank, (candidate, features, score) in enumerate(selected, start=1):
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "rank": rank,
                "score": f"{_submission_score(score, max_score):.6f}",
                "reasoning": build_reason(candidate, features, rank),
            }
        )
    return rows


def run_ranking(candidates_path: Path, out_path: Path, config: RankerConfig | None = None) -> RankingResult:
    config = config or RankerConfig()
    candidates = list(iter_candidates(candidates_path, max_candidates=config.max_candidates))
    ranked, used_backend = rank_candidates(candidates, config)
    # Consensus calibration pass (src/redrob_ranker/calibration.py): eight
    # evidence-backed pairwise preferences, official challenge JD only.
    if applies_to(config.jd):
        ranked = apply_calibration(ranked)
    top_k = min(config.top_k, len(ranked))
    rows = rows_from_ranked(ranked, top_k)
    # < 1.0 counts every honeypot-flagged candidate, whether hard-zeroed or
    # soft-floored at 0.05 (docs/honeypot_audit.md remediation).
    honeypots_detected = sum(1 for _, features, _ in ranked if features.honeypot_multiplier < 1.0)
    honeypots_in_output = sum(
        1 for _, features, _ in ranked[:top_k] if features.honeypot_multiplier < 1.0
    )
    errors = validate_rows(rows, expected=top_k)
    if errors:
        raise ValueError("Invalid generated submission:\n" + "\n".join(errors))
    write_submission(out_path, rows)
    return RankingResult(
        rows=rows,
        loaded_count=len(candidates),
        ranked_pool_count=len(ranked),
        bm25_backend=used_backend,
        honeypots_detected=honeypots_detected,
        honeypots_in_output=honeypots_in_output,
        raw_ranked=ranked,
    )
