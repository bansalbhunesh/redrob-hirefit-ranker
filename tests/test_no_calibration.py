#!/usr/bin/env python3
"""Verify that calibration.py is deleted and no hardcoded swaps exist."""

from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

def test_calibration_py_deleted():
    """calibration.py must not exist."""
    assert not (ROOT / "src" / "redrob_ranker" / "calibration.py").exists(), "calibration.py still exists. Delete it."

def test_no_hardcoded_swaps_in_scorer():
    """Scorer must not contain hardcoded candidate ID swaps."""
    scorer_path = ROOT / "src" / "redrob_ranker" / "scorer.py"
    if not scorer_path.exists():
        pytest.skip("scorer.py not found")

    content = scorer_path.read_text()
    
    # Check for suspicious patterns
    bad_patterns = [
        "candidate_id ==",
        "swap_ranks",
        "swap(",
        "calibration",
        "hardcoded",
    ]
    
    for pattern in bad_patterns:
        assert pattern not in content.lower(), f"scorer.py contains suspicious pattern: {pattern}"
