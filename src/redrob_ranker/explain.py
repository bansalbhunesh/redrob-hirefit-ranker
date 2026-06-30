"""Deterministic, exact explainability for the shipped evidence scorer.

For a linear (normalized weighted-sum) relevance, the Shapley value of each
feature is *exactly* its own additive term -- no sampling, no surrogate model,
no kernel approximation. So we can attribute every candidate's score to its
features byte-deterministically, which fits the golden-hash reproducibility
contract better than seed-variance SHAP/stability bands.

This module is OPT-IN and read-only with respect to ranking: it re-derives the
universal-v2 relevance (the base of the shipped frontier-v5 order) and never
mutates `CandidateFeatures` or the submission. Nothing here is imported by the
production path, so it cannot change the shipped byte output.

Two products:
  * `relevance_attributions` / `gate_log_effects` -- per-candidate decomposition
    (additive in score-space for relevance, additive in log-space for the
    multiplicative integrity gates). Sums back to the exact score.
  * `global_importance` -- mean |contribution| across the pool (the SHAP-summary
    equivalent), and `rank_stability` -- a label-free, deterministic rank band
    from leave-one-feature-out ablation (the confidence-interval equivalent).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from redrob_ranker.challenger import (
    UNIVERSAL_V2_BEHAVIOR_EXPONENT,
    UNIVERSAL_V2_TOTAL_WEIGHT,
    UNIVERSAL_V2_WEIGHTS,
)
from redrob_ranker.features import SEMANTIC_WEIGHT, clamp


@dataclass(slots=True)
class CandidateRecord:
    """Minimal, picklable view used for pool-level explanation."""

    candidate_id: str
    values: dict[str, float]
    retrieval_score: float = 0.0
    semantic_score: float | None = None
    behavioral_multiplier: float = 1.0
    honeypot_multiplier: float = 1.0
    disqualifier_multiplier: float = 1.0


def relevance_attributions(
    values: dict[str, float],
    retrieval_score: float,
    semantic_score: float | None = None,
    *,
    weights: dict[str, float] = UNIVERSAL_V2_WEIGHTS,
    total_weight: float = UNIVERSAL_V2_TOTAL_WEIGHT,
) -> tuple[dict[str, float], float]:
    """Exact additive decomposition of universal-v2 relevance.

    Returns (contributions, relevance) where sum(contributions.values()) ==
    relevance to floating-point exactness. Each contribution is that feature's
    Shapley value for the linear relevance map.
    """

    raw: dict[str, float] = {"bm25_score": weights["bm25_score"] * clamp(retrieval_score)}
    for name, weight in weights.items():
        if name == "bm25_score":
            continue
        raw[name] = weight * float(values.get(name, 0.0))

    denom = total_weight
    if semantic_score is not None:
        raw["semantic"] = SEMANTIC_WEIGHT * clamp(semantic_score)
        denom = total_weight + SEMANTIC_WEIGHT

    contributions = {name: term / denom for name, term in raw.items()}
    return contributions, sum(contributions.values())


def gate_log_effects(
    behavioral_multiplier: float,
    honeypot_multiplier: float,
    disqualifier_multiplier: float,
    *,
    exponent: float = UNIVERSAL_V2_BEHAVIOR_EXPONENT,
) -> dict[str, float]:
    """Additive (log-space) decomposition of the multiplicative gates.

    log(score) = log(relevance) + behavior + honeypot + disqualifier.
    A -inf entry means that gate hard-zeroed the candidate.
    """

    def safe_log(value: float) -> float:
        return math.log(value) if value > 0 else float("-inf")

    return {
        "behavior": exponent * safe_log(behavioral_multiplier),
        "honeypot": safe_log(honeypot_multiplier),
        "disqualifier": safe_log(disqualifier_multiplier),
    }


def final_score_from_relevance(
    relevance: float,
    behavioral_multiplier: float,
    honeypot_multiplier: float,
    disqualifier_multiplier: float,
    *,
    exponent: float = UNIVERSAL_V2_BEHAVIOR_EXPONENT,
) -> float:
    """Reconstruct the universal-v2 score from relevance + gates (matches challenger)."""

    return max(
        0.0,
        relevance
        * behavioral_multiplier**exponent
        * honeypot_multiplier
        * disqualifier_multiplier,
    )


def _record_relevance(rec: CandidateRecord, *, drop: str | None = None) -> float:
    """Relevance for one record, optionally with one feature ablated.

    Exploits linearity: dropping feature j subtracts its weighted term from the
    numerator and its weight from the denominator -- no full recompute needed.
    """

    contributions, relevance = relevance_attributions(
        rec.values, rec.retrieval_score, rec.semantic_score
    )
    if drop is None or drop not in contributions:
        return relevance
    # Undo normalization to operate on raw terms, then renormalize without `drop`.
    denom = UNIVERSAL_V2_TOTAL_WEIGHT + (
        SEMANTIC_WEIGHT if rec.semantic_score is not None else 0.0
    )
    weight = SEMANTIC_WEIGHT if drop == "semantic" else UNIVERSAL_V2_WEIGHTS.get(drop, 0.0)
    new_denom = denom - weight
    if new_denom <= 0:
        return 0.0
    raw_numerator = relevance * denom
    dropped_term = contributions[drop] * denom
    return (raw_numerator - dropped_term) / new_denom


def _ranked_ids(records: list[CandidateRecord], *, drop: str | None = None) -> list[str]:
    scored = [
        (
            final_score_from_relevance(
                _record_relevance(rec, drop=drop),
                rec.behavioral_multiplier,
                rec.honeypot_multiplier,
                rec.disqualifier_multiplier,
            ),
            rec.candidate_id,
        )
        for rec in records
    ]
    # Same ordering contract as the pipeline: score desc, id asc for ties.
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [cid for _, cid in scored]


def global_importance(records: list[CandidateRecord]) -> list[tuple[str, float]]:
    """Mean |contribution| per feature across the pool -- the SHAP-summary table."""

    totals: dict[str, float] = {}
    for rec in records:
        contributions, _ = relevance_attributions(
            rec.values, rec.retrieval_score, rec.semantic_score
        )
        for name, value in contributions.items():
            totals[name] = totals.get(name, 0.0) + abs(value)
    count = max(1, len(records))
    summary = [(name, total / count) for name, total in totals.items()]
    summary.sort(key=lambda item: -item[1])
    return summary


def rank_stability(
    records: list[CandidateRecord], *, top_k: int = 100
) -> dict[str, tuple[int, int, int]]:
    """Deterministic, label-free rank band for the top-k via leave-one-feature-out.

    For each weighted feature we re-rank the whole pool with that feature removed
    and record where each top-k candidate lands. Returns {id: (base_rank, lo, hi)}
    (1-indexed). A tight band == the candidate's position does not hinge on any
    single signal; a wide band flags a rank that one feature is carrying.
    """

    base = _ranked_ids(records)
    base_rank = {cid: i + 1 for i, cid in enumerate(base)}
    targets = base[:top_k]
    spread: dict[str, list[int]] = {cid: [base_rank[cid]] for cid in targets}

    ablatable = [name for name in UNIVERSAL_V2_WEIGHTS if name != "bm25_score"]
    for feature in ablatable:
        order = _ranked_ids(records, drop=feature)
        pos = {cid: i + 1 for i, cid in enumerate(order)}
        for cid in targets:
            spread[cid].append(pos[cid])

    return {
        cid: (base_rank[cid], min(positions), max(positions))
        for cid, positions in spread.items()
    }
