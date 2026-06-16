"""Central configuration for the judge-facing decision dashboard.

Import-light (NO streamlit) so it is testable and so production import-graph scans never
pull UI code. Holds verified artifact paths, canonical terminology, and the two-axis
integrity mapping. This module reads nothing and runs nothing in the production path.
"""
from __future__ import annotations

from pathlib import Path

# repo root = two levels up from this file (dashboard/constants.py -> repo root)
ROOT = Path(__file__).resolve().parent.parent

GOLDEN_COMMIT = "24f84f4b"   # main (HEAD 072707c): shipped = full-proof hedge sev<=1.2; golden af8f2b32 retained as fallback tag
GOLDEN_SHA256_PREFIX = "24f84f4b6160a4bc"   # shipped submission.csv hash (hedge); production pipeline reproduces golden af8f2b327f05d30e
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
    "metrics_manifest": ROOT / "docs/metrics_manifest.json",
}

# Canonical judge-facing facts. SINGLE SOURCE so the local dashboard and the HF Space
# cannot drift apart. Numbers with a manifest home (tests, honeypots) are read from
# docs/metrics_manifest.json at runtime; the rest are verified constants.
SHARED_FACTS = {
    "verdict": VERDICT,
    "golden_commit": GOLDEN_COMMIT,
    "honeypots_in_top100": 0,        # shipped detector — mirrors metrics_manifest.submission
    "honeypots_detected": 53,        # shipped detector total — mirrors metrics_manifest.submission
    "anachronism_anomalies_top100": 52,  # EXPERIMENTAL detector (NOT the shipped honeypot count)
    "psi_status": "AWAITING HUMAN DATA",
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
    "rerun, or influence the production ranking. Shipped submission 24f84f4b (severity-gated "
    "Copeland hedge) and all production "
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
