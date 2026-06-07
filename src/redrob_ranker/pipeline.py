"""End-to-end ranking pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from redrob_ranker.features import compute_features, final_score
from redrob_ranker.io import iter_candidates, write_submission
from redrob_ranker.reasoning import build_reason
from redrob_ranker.retrieval import Bm25Backend, retrieve_pool
from redrob_ranker.validation import validate_rows


def _submission_score(raw_score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    return max(0.0, min(raw_score / max_score, 1.0))


@dataclass(slots=True)
class RankerConfig:
    top_k: int = 100
    candidate_pool_size: int = 0
    max_candidates: int | None = None
    bm25_backend: Bm25Backend = "auto"


@dataclass(slots=True)
class RankingResult:
    rows: list[dict]
    loaded_count: int
    ranked_pool_count: int
    bm25_backend: str
    honeypots_detected: int
    honeypots_in_output: int
    raw_ranked: list[tuple[dict, object, float]] | None = None


def rank_candidates(candidates: list[dict], config: RankerConfig) -> tuple[list[tuple[dict, object, float]], str]:
    retrieval_scores, used_backend = retrieve_pool(
        candidates, config.candidate_pool_size, backend=config.bm25_backend
    )
    score_indices = (
        retrieval_scores.keys()
        if config.candidate_pool_size > 0
        else range(len(candidates))
    )

    ranked: list[tuple[dict, object, float]] = []
    for idx in score_indices:
        candidate = candidates[idx]
        features = compute_features(candidate)
        score = final_score(features, retrieval_scores.get(idx, 0.0))
        features.total = score
        ranked.append((candidate, features, score))

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
    top_k = min(config.top_k, len(ranked))
    rows = rows_from_ranked(ranked, top_k)
    honeypots_detected = sum(1 for _, features, _ in ranked if features.honeypot_multiplier <= 0.0)
    honeypots_in_output = sum(
        1 for _, features, _ in ranked[:top_k] if features.honeypot_multiplier <= 0.0
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
