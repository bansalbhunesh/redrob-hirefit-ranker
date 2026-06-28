"""End-to-end ranking pipeline."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from redrob_ranker.features import compute_features, final_score
from redrob_ranker.io import iter_candidates, write_submission
from redrob_ranker.reasoning import build_reason
from redrob_ranker.retrieval import Bm25Backend, retrieve_pool
from redrob_ranker.validation import validate_rows

# Import the shared cgroup helper. The underscore alias keeps existing test
# monkeypatches working without changes:
#   monkeypatch.setattr(pipeline_mod, "_cgroup_cpu_quota_count", lambda: 2)
from redrob_ranker._cgroup import cgroup_cpu_quota_count as _cgroup_cpu_quota_count

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
_WORKER_SCORING_PROFILE = "main"


def _init_worker(jd, scoring_profile: str = "main") -> None:
    global _WORKER_JD, _WORKER_SCORING_PROFILE
    _WORKER_JD = jd
    _WORKER_SCORING_PROFILE = scoring_profile


def _score_one(args: tuple[dict, float, float | None]) -> tuple[object, float]:
    """Top-level (picklable) worker: features + final score for one candidate.

    Deterministic and side-effect free, so running it in a process pool yields
    output identical to the serial path (verified byte-for-byte on the 100K pool).
    """
    candidate, retrieval_score, semantic_score = args
    features = compute_features(candidate, config=_WORKER_JD)
    if _WORKER_SCORING_PROFILE == "top23-clean":
        if _WORKER_JD is not None:
            raise ValueError("top23-clean currently supports only the bundled challenge JD")
        from redrob_ranker.challenger import top23_clean_score

        score = top23_clean_score(features, retrieval_score, semantic_score)
    else:
        score = final_score(features, retrieval_score, semantic_score, config=_WORKER_JD)
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
    # Opt-in experimental scorer. "main" preserves the shipped byte output.
    scoring_profile: str = "main"
    # Optional compiled JD (rank.py --jd). None = bundled challenge JD; the
    # None path is byte-identical to the historical pipeline.
    jd: object | None = None
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
    host_cpus = os.cpu_count() or 1
    available = min(host_cpus, _cgroup_cpu_quota_count() or host_cpus)
    if requested > 1:
        return max(1, min(requested, available))
    return max(1, min(_PARALLEL_WORKER_CAP, available))


def _resolve_chunksize(work_count: int, workers: int) -> int:
    """Return process-pool chunk size for feature scoring.

    Four chunks per worker keeps enough load-balancing headroom while cutting
    IPC/pickling overhead versus smaller chunks in constrained Docker runs.
    """
    return max(1, work_count // (workers * 4))


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
        global _WORKER_JD, _WORKER_SCORING_PROFILE
        prev_jd = _WORKER_JD
        prev_profile = _WORKER_SCORING_PROFILE
        _WORKER_JD = config.jd
        _WORKER_SCORING_PROFILE = config.scoring_profile
        try:
            for item in work:
                features, score = _score_one(item)
                ranked.append((item[0], features, score))
        finally:
            _WORKER_JD = prev_jd
            _WORKER_SCORING_PROFILE = prev_profile
    else:
        chunksize = _resolve_chunksize(len(work), workers)
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(config.jd, config.scoring_profile),
        ) as executor:
            results = executor.map(_score_one, work, chunksize=chunksize)
            for item, (features, score) in zip(work, results):
                ranked.append((item[0], features, score))

    if config.jd is not None:
        try:
            import numpy as np
            from redrob_ranker.moe_scorer import get_moe_scorer, INPUT_DIM
            moe = get_moe_scorer()
            fnames = [
                "core_skill_match", "jd_keyword_coverage_score", "nice_skill_match",
                "skill_depth_score", "endorsement_trust", "assessment_score_avg",
                "disqualifier_skill_flag", "keyword_stuffer_flag", "github_signal",
                "product_company_ratio", "consulting_only_flag", "ir_ranking_experience",
                "production_evidence", "title_match_score", "senior_title_held",
                "career_trajectory_score", "scale_signal", "code_writing_recent",
                "yoe_fit_score", "education_score", "ml_ai_tenure_score",
                "open_source_signal", "availability_score", "engagement_score",
                "responsiveness_score", "interview_reliability", "profile_quality",
                "notice_period_score", "location_score", "relocation_willing",
                "backend_depth_score", "data_bi_depth_score", "hyre_similarity"
            ][:INPUT_DIM]
            
            X = []
            for item in ranked:
                v = item[1].values
                vec = [v.get(fn, 0.0) for fn in fnames]
                X.append(vec)
            X = np.array(X)
            
            jd_text = config.jd.jd_query
            scores = moe.score_candidates(jd_text, X)
            
            # Update the scores in the ranked list
            ranked = [(item[0], item[1], float(scores[i])) for i, item in enumerate(ranked)]
        except Exception as e:
            print(f"MMoE scoring failed, falling back to heuristic stack: {e}")

    ranked.sort(key=lambda item: (-item[2], item[0]["candidate_id"]))
    return ranked, used_backend


def rows_from_ranked(ranked: list[tuple[dict, object, float]], top_k: int) -> list[dict]:
    rows: list[dict] = []
    selected = ranked[:top_k]
    max_score = selected[0][2] if selected else 0.0
    # Shared across the written rows so each gets a distinct verbatim career quote
    # (the synthetic pool reuses achievement strings; without this a top-100 sample
    # repeats the same sentence and reads as a template). Rank order = claim order.
    used_quotes: set[str] = set()
    for rank, (candidate, features, score) in enumerate(selected, start=1):
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "rank": rank,
                "score": f"{_submission_score(score, max_score):.6f}",
                "reasoning": build_reason(candidate, features, rank, used_quotes=used_quotes),
            }
        )
    return rows


def run_ranking(candidates_path: Path, out_path: Path, config: RankerConfig | None = None) -> RankingResult:
    config = config or RankerConfig()
    candidates = list(iter_candidates(candidates_path, max_candidates=config.max_candidates))
    ranked, used_backend = rank_candidates(candidates, config)
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
