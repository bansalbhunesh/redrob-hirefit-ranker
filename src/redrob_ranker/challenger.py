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

    weights = {
        name: weight * TOP23_FEATURE_MULTIPLIERS.get(name, 1.0)
        for name, weight in BASE_FEATURE_WEIGHTS.items()
    }
    total_weight = weights["bm25_score"]
    weighted_sum = weights["bm25_score"] * clamp(retrieval_score)
    for name, weight in weights.items():
        if name == "bm25_score":
            continue
        weighted_sum += weight * features.values.get(name, 0.0)
        total_weight += weight

    if semantic_score is not None:
        weighted_sum += SEMANTIC_WEIGHT * clamp(semantic_score)
        total_weight += SEMANTIC_WEIGHT

    relevance = weighted_sum / total_weight if total_weight else 0.0
    behavior = features.behavioral_multiplier ** TOP23_BEHAVIOR_EXPONENT
    return max(
        0.0,
        relevance
        * behavior
        * features.honeypot_multiplier
        * features.disqualifier_multiplier,
    )
