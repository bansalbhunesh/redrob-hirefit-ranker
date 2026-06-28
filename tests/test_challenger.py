from __future__ import annotations

import pytest

from redrob_ranker.challenger import top23_clean_score, universal_v2_score
from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import CandidateFeatures
from redrob_ranker.pipeline import RankerConfig, _init_worker, _score_one


def _features(**overrides: float) -> CandidateFeatures:
    values = {name: 0.5 for name in FEATURE_NAMES}
    values.update(overrides)
    return CandidateFeatures(
        candidate_id="CAND_0000001",
        values=values,
        behavioral_multiplier=0.4,
        honeypot_multiplier=1.0,
        disqualifier_multiplier=1.0,
    )


def test_challenger_rewards_direct_ranking_evidence() -> None:
    generic = _features(ir_ranking_experience=0.1, yoe_fit_score=0.4)
    proven = _features(ir_ranking_experience=1.0, yoe_fit_score=1.0)

    assert top23_clean_score(proven, 0.5) > top23_clean_score(generic, 0.5)


def test_challenger_ignores_assessment_score_for_rank() -> None:
    low = _features(assessment_score_avg=0.0)
    high = _features(assessment_score_avg=1.0)

    assert top23_clean_score(low, 0.5) == pytest.approx(top23_clean_score(high, 0.5))


def test_challenger_keeps_integrity_gates_multiplicative() -> None:
    clean = _features()
    honeypot = _features()
    honeypot.honeypot_multiplier = 0.0

    assert top23_clean_score(clean, 0.5) > 0.0
    assert top23_clean_score(honeypot, 0.5) == 0.0


def test_universal_v2_rewards_production_evidence() -> None:
    unproven = _features(production_evidence=0.0, yoe_fit_score=0.4)
    proven = _features(production_evidence=1.0, yoe_fit_score=1.0)

    assert universal_v2_score(proven, 0.5) > universal_v2_score(unproven, 0.5)


def test_universal_v2_keeps_integrity_gates_multiplicative() -> None:
    clean = _features()
    disqualified = _features()
    disqualified.disqualifier_multiplier = 0.0

    assert universal_v2_score(clean, 0.5) > 0.0
    assert universal_v2_score(disqualified, 0.5) == 0.0


def test_pipeline_selects_challenger_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = {
        "candidate_id": "CAND_0000001",
        "profile": {"current_title": "Senior ML Engineer", "years_of_experience": 7},
        "career_history": [],
        "skills": [],
        "redrob_signals": {},
    }
    monkeypatch.setattr("redrob_ranker.pipeline.compute_features", lambda *_args, **_kwargs: _features())
    _init_worker(None, RankerConfig(scoring_profile="top23-clean").scoring_profile)

    features, score = _score_one((candidate, 0.5, None))

    assert features.total == score
    assert score == pytest.approx(top23_clean_score(features, 0.5))
    _init_worker(None, "main")


def test_pipeline_selects_universal_v2_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = {
        "candidate_id": "CAND_0000001",
        "profile": {"current_title": "Senior ML Engineer", "years_of_experience": 7},
        "career_history": [],
        "skills": [],
        "redrob_signals": {},
    }
    monkeypatch.setattr("redrob_ranker.pipeline.compute_features", lambda *_args, **_kwargs: _features())
    _init_worker(None, "universal-v2")

    features, score = _score_one((candidate, 0.5, None))

    assert features.total == score
    assert score == pytest.approx(universal_v2_score(features, 0.5))
    _init_worker(None, "main")
