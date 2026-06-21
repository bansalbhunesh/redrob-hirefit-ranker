"""End-to-end v2 ranking pipeline (learned ranker).

Flow: load -> BM25 retrieve (also caches candidate text) -> extract the shared
33-feature vector per candidate -> learned relevance -> integrity gate -> sort
-> top-k with grounded reasoning. Deterministic: ties break by candidate_id
ascending, matching the official validator.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from redrob_ranker.features import compute_features
from redrob_ranker.io import iter_candidates, write_submission
from redrob_ranker.reasoning import build_reason
from redrob_ranker.retrieval import retrieve_pool
from redrob_ranker.validation import validate_rows
from redrob_ranker.constants import FEATURE_NAMES

from redrob_ranker_v2.model import LearnedRanker


@dataclass(slots=True)
class RankingResultV2:
    rows: list[dict]
    loaded_count: int
    ranked_pool_count: int
    bm25_backend: str
    model_kind: str
    honeypots_in_output: int
    raw_ranked: list[tuple[dict, object, float]]


def _build_matrix(ranked_feats: list, retrieval_scores: dict[int, float]) -> np.ndarray:
    n = len(ranked_feats)
    X = np.empty((n, len(FEATURE_NAMES) + 1), dtype=np.float64)
    for i, (idx, feats) in enumerate(ranked_feats):
        for j, name in enumerate(FEATURE_NAMES):
            X[i, j] = feats.values.get(name, 0.0)
        X[i, len(FEATURE_NAMES)] = retrieval_scores.get(idx, 0.0)
    return X


def _submission_score(raw: float, mx: float) -> float:
    if mx <= 0:
        return 0.0
    return max(0.0, min(raw / mx, 1.0))


def run_ranking_v2(
    candidates_path: Path,
    out_path: Path,
    top_k: int = 100,
    model_path: Path | None = None,
    max_candidates: int | None = None,
) -> RankingResultV2:
    candidates = list(iter_candidates(candidates_path, max_candidates=max_candidates))
    retrieval_scores, backend = retrieve_pool(candidates, 0)

    ranked_feats: list[tuple[int, object]] = []
    gates: list[float] = []
    for idx, cand in enumerate(candidates):
        feats = compute_features(cand)
        ranked_feats.append((idx, feats))
        gates.append(feats.honeypot_multiplier * feats.disqualifier_multiplier)

    X = _build_matrix(ranked_feats, retrieval_scores)
    ranker = LearnedRanker(model_path)
    scores = ranker.score(X, np.asarray(gates, dtype=np.float64))

    order = sorted(
        range(len(candidates)),
        key=lambda i: (-float(scores[i]), candidates[i]["candidate_id"]),
    )
    raw_ranked = [
        (candidates[i], ranked_feats[i][1], float(scores[i])) for i in order
    ]

    k = min(top_k, len(raw_ranked))
    selected = raw_ranked[:k]
    mx = selected[0][2] if selected else 0.0
    used_quotes: set[str] = set()
    rows: list[dict] = []
    for rank, (cand, feats, sc) in enumerate(selected, start=1):
        rows.append(
            {
                "candidate_id": cand["candidate_id"],
                "rank": rank,
                "score": f"{_submission_score(sc, mx):.6f}",
                "reasoning": build_reason(cand, feats, rank, used_quotes=used_quotes),
            }
        )

    errors = validate_rows(rows, expected=k)
    if errors:
        raise ValueError("Invalid generated submission:\n" + "\n".join(errors))
    write_submission(out_path, rows)

    honeypots_in_output = sum(
        1 for _, feats, _ in selected if feats.honeypot_multiplier < 1.0
    )
    return RankingResultV2(
        rows=rows,
        loaded_count=len(candidates),
        ranked_pool_count=len(raw_ranked),
        bm25_backend=backend,
        model_kind=ranker.kind,
        honeypots_in_output=honeypots_in_output,
        raw_ranked=raw_ranked,
    )
