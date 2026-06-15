"""Central configuration for the judge-facing decision dashboard.

Import-light (NO streamlit) so it is testable and so production import-graph scans never
pull UI code. Holds verified artifact paths, canonical terminology, and the two-axis
integrity mapping. This module reads nothing and runs nothing in the production path.
"""
from __future__ import annotations

from pathlib import Path

# repo root = two levels up from this file (dashboard/constants.py -> repo root)
ROOT = Path(__file__).resolve().parent.parent

GOLDEN_COMMIT = "af8f2b32"
GOLDEN_SHA256_PREFIX = "af8f2b327f05d30e"   # submission.csv golden hash (verify, do not invent)
VERDICT = "NO_RANKING_DOMINATES"

# Verified local artifact paths (committed). Loaders degrade gracefully if any is absent.
CONFIG = {
    "omega_decision": ROOT / "experiments/omega_outputs/decision.json",
    "omega_frontier": ROOT / "experiments/omega_outputs/minimax_regret_frontier.json",
    "omega_posteriors": ROOT / "experiments/omega_outputs/posteriors.json",
    "omega_causal": ROOT / "experiments/omega_outputs/causal_effects.json",
    "integrity_cards": ROOT / "docs/human_opinion/integrity_cards.json",
    "phi_corpus": ROOT / "docs/human_opinion/corpus_phi2.csv",
    "phi_manifest": ROOT / "docs/human_opinion/corpus_phi2_manifest.json",
    "psi_manifest": ROOT / "experiments/psi_panel/manifest.json",
    "disagreement_manifest": ROOT / "experiments/disagreement_set/manifest.json",
    "registry": ROOT / "experiments/registry.json",
}

# Canonical terminology — never used interchangeably (scientific-honesty requirement).
TERMS = {
    "shipped_detector": "shipped honeypot detector",
    "anachronism": "experimental anachronism detector",
    "anomaly": "detector-flagged anomaly",
    "confirmed": "confirmed hard contradiction",
    "official": "official planted honeypot",
}

# Two-axis integrity mapping validated by Study Φ (evidence status -> recommended action).
EVIDENCE_TO_ACTION = {
    "CLEAR": "CONTINUE",
    "AMBIGUOUS": "CLARIFY",
    "PROBABLE_CONTRADICTION": "VERIFY",     # NOT BLOCK
    "CONFIRMED_CONTRADICTION": "BLOCK",
}
EVIDENCE_ORDER = ["CLEAR", "AMBIGUOUS", "PROBABLE_CONTRADICTION", "CONFIRMED_CONTRADICTION"]
ACTION_ORDER = ["CONTINUE", "CLARIFY", "VERIFY", "DOWNRANK", "BLOCK"]

STATUS_COLORS = {"PASS": "#1b8a5a", "PENDING": "#c98a00", "FAIL": "#b22222", "INFO": "#444"}

DISCLAIMER = (
    "This dashboard is a downstream research and explanation layer. It does not modify, "
    "rerun, or influence the production ranking. Golden submission af8f2b32 and all production "
    "files remain byte-identical."
)
VERDICT_DISCLAIMER = (
    "NO_RANKING_DOMINATES does not mean the rankings are equal. It means no alternative has "
    "satisfied every preregistered shipping gate using independent evidence."
)
EXPERIMENTAL_INTEGRITY_NOTE = (
    "Experimental integrity guidance. VERIFY recommends human review and does NOT identify "
    "confirmed fraud or automatically change the candidate's rank."
)

# Shipping-gate battery (4 computational + 1 human). PENDING is not a model failure.
GATES = [
    ("Lower simulated worst-case regret", "PASS",
     "Ω has the lowest max-regret across simulated integrity-aversion worlds (by construction)."),
    ("Stable under reviewer-family deletion", "PASS",
     "Decision framework stable in simulated sensitivity analysis (SPA 0.789 -> 0.762)."),
    ("Not dominated by one candidate", "PASS",
     "Ω worst-case advantage is not carried by a single candidate (influence test)."),
    ("Zero CONFIRMED hard contradictions in protected ranks", "PASS",
     "No candidate is independently confirmed as a hard contradiction (top-10/top-100)."),
    ("Independent human lockbox (Ψ)", "PENDING",
     "Ψ has no human responses yet — unmet BY CONSTRUCTION, not a performance failure."),
]
