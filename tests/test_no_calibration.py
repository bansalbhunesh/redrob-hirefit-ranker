#!/usr/bin/env python3
"""Verify that calibration.py is deleted and no hardcoded-swap logic exists."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_calibration_py_deleted():
    """calibration.py must not exist."""
    assert not (ROOT / "src" / "redrob_ranker" / "calibration.py").exists(), (
        "calibration.py still exists. Delete it."
    )


def test_no_calibration_or_swap_logic_in_scorer():
    """The live scoring modules must contain no calibration / hardcoded-swap logic.

    Replaces an earlier test that pointed at a non-existent ``scorer.py`` and
    therefore always skipped (giving false assurance). This scans the real
    scoring modules instead, so reintroducing calibration or row-swap logic
    fails CI.
    """
    src = ROOT / "src" / "redrob_ranker"
    bad_patterns = ["calibration", "swap_ranks", "calibration_preferences", "hardcoded"]
    for module in ("features.py", "pipeline.py"):
        path = src / module
        assert path.exists(), f"expected scoring module missing: {module}"
        content = path.read_text(encoding="utf-8").lower()
        for pattern in bad_patterns:
            assert pattern not in content, (
                f"{module} contains suspicious pattern: {pattern!r}"
            )
