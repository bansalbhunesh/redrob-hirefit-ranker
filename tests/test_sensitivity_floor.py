"""The behavioral-floor parameter must default to shipped behavior exactly."""

from __future__ import annotations

import math

from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import (
    BEHAVIORAL_FLOOR_DEFAULT,
    compute_behavioral_multiplier,
)


def _values(**over) -> dict[str, float]:
    v = {name: 0.0 for name in FEATURE_NAMES}
    v.update(over)
    return v


GOOD = {
    "signals": {
        "open_to_work_flag": True,
        "saved_by_recruiters_30d": 7,
        "notice_period_days": 20,
    },
    "values": dict(
        responsiveness_score=0.9,
        profile_quality=0.9,
        availability_score=1.0,
        interview_reliability=0.95,
        github_signal=0.4,
        notice_period_score=1.0,
    ),
}

BAD = {
    "signals": {
        "open_to_work_flag": False,
        "saved_by_recruiters_30d": 0,
        "notice_period_days": 180,
    },
    "values": dict(
        responsiveness_score=0.0,
        profile_quality=0.0,
        availability_score=0.0,
        interview_reliability=0.0,
        github_signal=0.0,
        notice_period_score=0.1,
    ),
}


def _mult(profile, floor=None):
    candidate = {"redrob_signals": profile["signals"]}
    values = _values(**profile["values"])
    if floor is None:
        return compute_behavioral_multiplier(values, candidate)
    return compute_behavioral_multiplier(values, candidate, floor=floor)


def test_default_floor_constant_is_shipped_value():
    assert BEHAVIORAL_FLOOR_DEFAULT == 0.25


def test_default_call_identical_to_explicit_floor():
    for profile in (GOOD, BAD):
        assert _mult(profile) == _mult(profile, floor=0.25)


def test_bad_profile_hits_floor_exactly():
    assert _mult(BAD) == 0.25
    assert _mult(BAD, floor=0.55) == 0.55
    assert _mult(BAD, floor=1.00) == 1.00


def test_raising_floor_equals_max_of_clamped_and_floor():
    # The arithmetic identity the sweep relies on.
    for profile in (GOOD, BAD):
        base = _mult(profile)
        for floor in (0.40, 0.55, 0.70, 0.85, 1.00):
            assert math.isclose(_mult(profile, floor=floor), max(base, floor))


def test_good_profile_unaffected_by_floor():
    base = _mult(GOOD)
    assert base > 0.85
    assert _mult(GOOD, floor=0.85) == base
