"""Integrity audit-card logic (import-light; NO streamlit). The canonical two-axis mapping
and read-only helpers over the committed integrity_cards.json. Pure functions so the mapping
is unit-testable independent of the UI and of production.
"""
from __future__ import annotations

from collections import Counter

from dashboard.constants import EVIDENCE_TO_ACTION
from dashboard.data_loader import load_json_safe

# Phrases that would falsely assert ground truth we do not have. Cards must never use them.
FORBIDDEN_CLAIMS = ("official planted honeypot", "confirmed fraud", "fraudulent candidate",
                    "is a honeypot", "known honeypot id")


def action_for(evidence_status: str) -> str:
    """Canonical Φ-validated mapping. PROBABLE_CONTRADICTION -> VERIFY (never BLOCK)."""
    return EVIDENCE_TO_ACTION.get(evidence_status, "CLARIFY")


def load_cards(path) -> list[dict]:
    art = load_json_safe(path)
    return art.data if art.ok and isinstance(art.data, list) else []


def distribution(cards: list[dict]) -> dict:
    return dict(Counter((c.get("evidence_status"), c.get("recommended_action")) for c in cards))


def mapping_is_consistent(cards: list[dict]) -> bool:
    """Every card's action must equal the canonical mapping of its evidence status."""
    return all(c.get("recommended_action") == action_for(c.get("evidence_status")) for c in cards)


def no_forbidden_claims(cards: list[dict]) -> bool:
    blob = " ".join(
        (str(c.get("reason", "")) + " " + str(c.get("verification_request", ""))).lower()
        for c in cards)
    return not any(f in blob for f in FORBIDDEN_CLAIMS)
