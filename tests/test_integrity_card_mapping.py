"""Integrity-card two-axis mapping is correct and makes no unfounded ground-truth claims."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.constants import CONFIG, EVIDENCE_TO_ACTION  # noqa: E402
from dashboard.integrity_cards import (action_for, distribution, load_cards,  # noqa: E402
                                       mapping_is_consistent, no_forbidden_claims)


def test_canonical_mapping():
    assert action_for("CLEAR") == "CONTINUE"
    assert action_for("AMBIGUOUS") == "CLARIFY"
    assert action_for("PROBABLE_CONTRADICTION") == "VERIFY"
    assert action_for("CONFIRMED_CONTRADICTION") == "BLOCK"


def test_probable_is_verify_not_block():
    assert EVIDENCE_TO_ACTION["PROBABLE_CONTRADICTION"] == "VERIFY"
    assert EVIDENCE_TO_ACTION["PROBABLE_CONTRADICTION"] != "BLOCK"


def test_real_cards_mapping_consistent():
    cards = load_cards(CONFIG["integrity_cards"])
    assert cards, "integrity_cards.json should be present"
    assert mapping_is_consistent(cards)


def test_no_candidate_called_official_honeypot():
    cards = load_cards(CONFIG["integrity_cards"])
    assert no_forbidden_claims(cards), "cards must not assert official-honeypot / confirmed-fraud"


def test_distribution_matches_known_shape():
    cards = load_cards(CONFIG["integrity_cards"])
    dist = distribution(cards)
    # 52 PROBABLE->VERIFY, 45 CLEAR->CONTINUE, 3 AMBIGUOUS->CLARIFY, 0 CONFIRMED->BLOCK
    assert dist.get(("PROBABLE_CONTRADICTION", "VERIFY")) == 52
    assert dist.get(("CONFIRMED_CONTRADICTION", "BLOCK"), 0) == 0
