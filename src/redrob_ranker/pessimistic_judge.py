#!/usr/bin/env python3
"""
Synthetic Pessimistic Judge (Option B)

Uses the SAME rich features as your linear scorer, but applies them
via MULTIPLICATIVE gates and HARD thresholds. This creates a harder
label distribution that forces LightGBM to learn non-linear interactions.

Validated against the 8 LLM-verified calibration pairs.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from .features import CandidateFeatures, compute_features
from .constants import FEATURE_NAMES


@dataclass
class PessimisticJudgment:
    """Output of the pessimistic judge."""
    score: float                  # 0.0 to 1.0
    passed_gates: List[str]       # Which gates were passed
    failed_gate: Optional[str]    # First gate that failed (if any)
    gate_scores: Dict[str, float] # Per-gate intermediate scores


class PessimisticJudge:
    """
    A judge that is HARDER than the linear scorer.

    Logic:
    1. Honeypot gate: zero-tolerance. Any trap = instant 0.0.
    2. Title gate: multiplicative penalty. Bad title = near-zero.
    3. Role-depth gate: must have minimum depth for the role family.
    4. Production gate: must show shipped code/systems.
    5. Behavioral gate: strict availability check.
    6. Consensus score: multiplicative combination of surviving features.

    This is NOT a linear weighted sum. It is a cascade of multiplicative
    filters that models how a skeptical senior recruiter actually thinks.
    """

    def __init__(self, role_family: str = "ai_ml_engineering"):
        self.role_family = role_family

        # --- Gate thresholds (tuned to be pessimistic) ---
        self.thresholds = {
            # Gate 1: Honeypot
            "honeypot_min": 0.05,       # Below this = trap

            # Gate 2: Title
            "title_min": 0.25,          # Below this = wrong role
            "title_ideal": 0.80,        # Above this = full credit

            # Gate 3: Role depth
            "backend_depth_min": 0.35,
            "data_bi_depth_min": 0.35,
            "devops_depth_min": 0.30,
            "search_depth_min": 0.40,
            "ai_depth_min": 0.30,

            # Gate 4: Production evidence
            "production_min": 0.15,
            "production_ideal": 0.50,

            # Gate 5: Behavioral
            "response_rate_min": 0.20,
            "notice_max_days": 120,
        }

    def judge(self, candidate: dict) -> PessimisticJudgment:
        """Run the pessimistic judge on a single candidate."""
        features = compute_features(candidate)
        gates = {}
        passed = []

        # ================================================================
        # GATE 1: HONEYPOT (ZERO TOLERANCE)
        # ================================================================
        if features.honeypot_multiplier <= 0.0:
            return PessimisticJudgment(
                score=0.0,
                passed_gates=[],
                failed_gate="honeypot_hard_zero",
                gate_scores={"honeypot": features.honeypot_multiplier}
            )

        # Softened honeypot class (0.05-0.20) gets penalized but not killed
        honeypot_penalty = features.honeypot_multiplier
        if honeypot_penalty < 0.20:
            gates["honeypot"] = honeypot_penalty
            passed.append("honeypot_soft")
        else:
            gates["honeypot"] = 1.0
            passed.append("honeypot_clean")

        # ================================================================
        # GATE 2: TITLE ALIGNMENT (MULTIPLICATIVE)
        # ================================================================
        title_score = features.values.get("title_match_score", 0.0)

        if title_score < self.thresholds["title_min"]:
            # Wrong role - not a complete reject, but heavily penalized
            gates["title"] = 0.10
            passed.append("title_weak")
        elif title_score < self.thresholds["title_ideal"]:
            # Adjacent role - partial credit
            gates["title"] = 0.40 + (title_score - self.thresholds["title_min"]) * 0.80
            passed.append("title_adjacent")
        else:
            gates["title"] = 1.0
            passed.append("title_strong")

        # ================================================================
        # GATE 3: ROLE-SPECIFIC DEPTH (HARD MINIMUM)
        # ================================================================
        depth_score = 0.0
        depth_min = 0.0

        if self.role_family == "backend_engineering":
            depth_score = features.values.get("backend_depth_score", 0.0)
            depth_min = self.thresholds["backend_depth_min"]
        elif self.role_family == "data_bi_analytics":
            depth_score = features.values.get("data_bi_depth_score", 0.0)
            depth_min = self.thresholds["data_bi_depth_min"]
        elif self.role_family == "devops_cloud":
            depth_score = features.values.get("devops_depth_score", 0.0)
            depth_min = self.thresholds["devops_depth_min"]
        elif self.role_family == "search_relevance":
            depth_score = features.values.get("search_depth_score", 0.0)
            depth_min = self.thresholds["search_depth_min"]
        else:  # ai_ml_engineering
            depth_score = features.values.get("skill_depth_score", 0.0)
            depth_min = self.thresholds["ai_depth_min"]

        if depth_score < depth_min:
            # Below minimum depth - heavily penalized but not killed
            # (A junior with strong other signals might still pass)
            gates["role_depth"] = 0.20 + (depth_score / depth_min) * 0.30
            passed.append("role_depth_below_min")
        else:
            gates["role_depth"] = 0.50 + (depth_score - depth_min) / (1.0 - depth_min) * 0.50
            passed.append("role_depth_ok")

        # ================================================================
        # GATE 4: PRODUCTION EVIDENCE (MULTIPLICATIVE)
        # ================================================================
        prod = features.values.get("production_evidence", 0.0)

        if prod < self.thresholds["production_min"]:
            gates["production"] = 0.15
            passed.append("production_weak")
        elif prod < self.thresholds["production_ideal"]:
            gates["production"] = 0.40 + (prod - self.thresholds["production_min"]) / (self.thresholds["production_ideal"] - self.thresholds["production_min"]) * 0.60
            passed.append("production_moderate")
        else:
            gates["production"] = 1.0
            passed.append("production_strong")

        # ================================================================
        # GATE 5: BEHAVIORAL / AVAILABILITY (STRICT)
        # ================================================================
        beh_score = 1.0

        # Open to work
        if not candidate.get("open_to_work", True):
            beh_score *= 0.70
            passed.append("not_otw")
        else:
            passed.append("otw")

        # Response rate
        if candidate.get("recruiter_response_rate", 1.0) < self.thresholds["response_rate_min"]:
            beh_score *= 0.60
            passed.append("low_response")
        else:
            passed.append("good_response")

        # Notice period
        notice_score = features.values.get("notice_period_score", 1.0)
        if notice_score < 0.0:  # Long notice
            beh_score *= 0.80
            passed.append("long_notice")
        else:
            passed.append("short_notice")

        gates["behavioral"] = beh_score

        # ================================================================
        # GATE 6: SKILL CORE (MULTIPLICATIVE, NOT ADDITIVE)
        # ================================================================
        # Core skill match is the foundation, but it interacts with production
        core = features.values.get("core_skill_match", 0.0)

        # If core is high but production is low = academic/research type
        # If core is moderate but production is high = strong practitioner
        # Multiplicative interaction captures this
        skill_prod_interaction = core * gates["production"]

        if skill_prod_interaction < 0.10:
            gates["skill_core"] = 0.20
            passed.append("skill_weak")
        elif skill_prod_interaction < 0.30:
            gates["skill_core"] = 0.50
            passed.append("skill_moderate")
        else:
            gates["skill_core"] = 0.70 + skill_prod_interaction * 0.30
            passed.append("skill_strong")

        # ================================================================
        # FINAL CONSENSUS: MULTIPLICATIVE COMBINATION
        # ================================================================
        # This is the KEY difference from the linear scorer.
        # The linear scorer does: w1*f1 + w2*f2 + ...
        # The pessimistic judge does: f1 * f2 * f3 * ...
        # This creates a much harder, more selective distribution.

        final_score = (
            gates["honeypot"] *
            gates["title"] *
            gates["role_depth"] *
            gates["production"] *
            gates["behavioral"] *
            gates["skill_core"]
        )

        # Boost for exceptional candidates (all gates strong)
        if all(g >= 0.80 for g in [gates["title"], gates["role_depth"],
                                   gates["production"], gates["skill_core"]]):
            final_score = min(final_score * 1.15, 1.0)
            passed.append("exceptional_boost")

        return PessimisticJudgment(
            score=round(final_score, 4),
            passed_gates=passed,
            failed_gate=None,
            gate_scores=gates
        )


# --- Convenience function for batch processing ---
def batch_judge(candidates: List[dict], role_family: str = "ai_ml_engineering") -> List[PessimisticJudgment]:
    """Judge a batch of candidates."""
    judge = PessimisticJudge(role_family)
    return [judge.judge(c) for c in candidates]
