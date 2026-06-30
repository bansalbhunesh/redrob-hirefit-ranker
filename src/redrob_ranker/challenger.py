"""Clean-room scorer distilled from public Redrob ranking patterns.

This module intentionally contains no competitor code, candidate IDs, public
submission ranks, or pool-specific paragraph fingerprints.  It changes only
the relative emphasis of features already produced by HireFit:

* direct information-retrieval/ranking career evidence;
* the Senior-AI experience band and senior-title evidence;
* location fit;
* a gentler availability multiplier.

The default scorer remains unchanged.  This profile is opt-in while it passes
the full reproducibility, integrity, runtime, and external-label gates.
"""

from __future__ import annotations

from redrob_ranker.constants import BASE_FEATURE_WEIGHTS
from redrob_ranker.features import CandidateFeatures, SEMANTIC_WEIGHT, clamp


TOP23_FEATURE_MULTIPLIERS: dict[str, float] = {
    "ir_ranking_experience": 1.50,
    "yoe_fit_score": 2.00,
    "location_score": 1.50,
    "senior_title_held": 1.50,
    # Public winners consistently separate career evidence from a broad skill
    # inventory.  Keep the signal, but stop it from dominating the shortlist.
    "core_skill_match": 0.50,
    # Public assessment scores were negatively associated with the consensus
    # additions.  Until outcome-calibrated labels exist, do not use them to
    # decide rank; assessment contradictions remain integrity guardrails.
    "assessment_score_avg": 0.00,
}

# Winners use availability as a deal-breaker/nudge rather than allowing it to
# overwhelm role evidence.  Raising a [0.25, 1.10] multiplier to this exponent
# keeps ordering signal while compressing its range to roughly [0.62, 1.03].
TOP23_BEHAVIOR_EXPONENT = 0.35


# Second clean-room hypothesis, selected only after a broad public-technique
# audit and a 15-label multi-objective search.  It deliberately remains a
# small, inspectable evidence model rather than a pool-specific lookup or a
# copied competitor ranker.
UNIVERSAL_V2_FEATURE_MULTIPLIERS: dict[str, float] = {
    "ir_ranking_experience": 0.83527,
    "yoe_fit_score": 4.30920,
    "location_score": 0.67094,
    "senior_title_held": 1.40042,
    "core_skill_match": 0.46425,
    "assessment_score_avg": 0.18542,
    "production_evidence": 2.35747,
    "career_trajectory_score": 0.40158,
    "product_company_ratio": 1.45178,
    "skill_depth_score": 1.68406,
}

UNIVERSAL_V2_BEHAVIOR_EXPONENT = 0.31065


def _scaled_weights(multipliers: dict[str, float]) -> dict[str, float]:
    return {
        name: weight * multipliers.get(name, 1.0)
        for name, weight in BASE_FEATURE_WEIGHTS.items()
    }


def _total_weight(weights: dict[str, float]) -> float:
    # Preserve the scorer's historical addition order for bit-exact output.
    total = weights["bm25_score"]
    for name, weight in weights.items():
        if name != "bm25_score":
            total += weight
    return total


TOP23_WEIGHTS = _scaled_weights(TOP23_FEATURE_MULTIPLIERS)
TOP23_TOTAL_WEIGHT = _total_weight(TOP23_WEIGHTS)
UNIVERSAL_V2_WEIGHTS = _scaled_weights(UNIVERSAL_V2_FEATURE_MULTIPLIERS)
UNIVERSAL_V2_TOTAL_WEIGHT = _total_weight(UNIVERSAL_V2_WEIGHTS)
MAIN_TOTAL_WEIGHT = _total_weight(BASE_FEATURE_WEIGHTS)


def _weighted_profile_score(
    features: CandidateFeatures,
    retrieval_score: float,
    semantic_score: float | None,
    weights: dict[str, float],
    total_weight: float,
    behavior_exponent: float,
) -> float:
    """Apply an auditable evidence blend while preserving hard guardrails."""

    weighted_sum = weights["bm25_score"] * clamp(retrieval_score)
    for name, weight in weights.items():
        if name == "bm25_score":
            continue
        weighted_sum += weight * features.values.get(name, 0.0)

    if semantic_score is not None:
        weighted_sum += SEMANTIC_WEIGHT * clamp(semantic_score)
        total_weight += SEMANTIC_WEIGHT

    relevance = weighted_sum / total_weight if total_weight else 0.0
    behavior = features.behavioral_multiplier**behavior_exponent
    return max(
        0.0,
        relevance
        * behavior
        * features.honeypot_multiplier
        * features.disqualifier_multiplier,
    )


def top23_clean_score(
    features: CandidateFeatures,
    retrieval_score: float = 0.0,
    semantic_score: float | None = None,
) -> float:
    """Return the opt-in public-pattern challenger score.

    Honeypot and disqualifier multipliers are deliberately unchanged.  A
    cleaner relevance blend must never rescue a profile that fails HireFit's
    existing integrity gates.
    """

    return _weighted_profile_score(
        features,
        retrieval_score,
        semantic_score,
        TOP23_WEIGHTS,
        TOP23_TOTAL_WEIGHT,
        TOP23_BEHAVIOR_EXPONENT,
    )


def universal_v2_score(
    features: CandidateFeatures,
    retrieval_score: float = 0.0,
    semantic_score: float | None = None,
) -> float:
    """Return the multi-evaluator clean-room evidence scorer.

    The model emphasizes demonstrated production work and appropriate
    experience more than broad keyword inventories.  Availability remains a
    nudge, while the existing honeypot and disqualifier gates remain exact.
    """

    return _weighted_profile_score(
        features,
        retrieval_score,
        semantic_score,
        UNIVERSAL_V2_WEIGHTS,
        UNIVERSAL_V2_TOTAL_WEIGHT,
        UNIVERSAL_V2_BEHAVIOR_EXPONENT,
    )


def universal_v2_and_main_score(
    features: CandidateFeatures,
    retrieval_score: float = 0.0,
    semantic_score: float | None = None,
) -> tuple[float, float]:
    """Compute V2 and its V3/V4/V5 main-score feature in one exact pass."""

    retrieval = clamp(retrieval_score)
    universal_sum = UNIVERSAL_V2_WEIGHTS["bm25_score"] * retrieval
    main_sum = BASE_FEATURE_WEIGHTS["bm25_score"] * retrieval
    for name, main_weight in BASE_FEATURE_WEIGHTS.items():
        if name == "bm25_score":
            continue
        value = features.values.get(name, 0.0)
        universal_sum += UNIVERSAL_V2_WEIGHTS[name] * value
        main_sum += main_weight * value

    universal_total = UNIVERSAL_V2_TOTAL_WEIGHT
    main_total = MAIN_TOTAL_WEIGHT
    if semantic_score is not None:
        semantic = SEMANTIC_WEIGHT * clamp(semantic_score)
        universal_sum += semantic
        main_sum += semantic
        universal_total += SEMANTIC_WEIGHT
        main_total += SEMANTIC_WEIGHT

    universal_relevance = universal_sum / universal_total
    main_relevance = main_sum / main_total
    universal = max(
        0.0,
        universal_relevance
        * features.behavioral_multiplier**UNIVERSAL_V2_BEHAVIOR_EXPONENT
        * features.honeypot_multiplier
        * features.disqualifier_multiplier,
    )
    main = max(
        0.0,
        main_relevance
        * features.behavioral_multiplier
        * features.honeypot_multiplier
        * features.disqualifier_multiplier,
    )
    return universal, main
