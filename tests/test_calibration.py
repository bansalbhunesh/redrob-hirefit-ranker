"""Consensus calibration pass: semantics and safety gates."""

from redrob_ranker.calibration import (
    CALIBRATION_PREFERENCES,
    applies_to,
    apply_calibration,
)
import redrob_ranker.pipeline as pipeline_mod
from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import CandidateFeatures
from redrob_ranker.pipeline import RankerConfig, run_ranking


def _item(cid: str, score: float):
    return ({"candidate_id": cid}, object(), score)


def test_preferences_are_eight_unique_ids():
    assert len(CALIBRATION_PREFERENCES) == 8
    ids = [cid for pair in CALIBRATION_PREFERENCES for cid in pair]
    assert len(ids) == len(set(ids)) == 16


def test_misordered_pair_is_exchanged_and_scores_stay_positional():
    preferred, deferred = CALIBRATION_PREFERENCES[0]
    ranked = [_item(deferred, 0.9), _item("CAND_0000001", 0.8), _item(preferred, 0.7)]
    out = apply_calibration(ranked)
    assert [it[0]["candidate_id"] for it in out] == [preferred, "CAND_0000001", deferred]
    # The descending score ladder stays attached to positions.
    assert [it[2] for it in out] == [0.9, 0.8, 0.7]


def test_already_correct_order_is_untouched():
    preferred, deferred = CALIBRATION_PREFERENCES[0]
    ranked = [_item(preferred, 0.9), _item(deferred, 0.8)]
    out = apply_calibration(ranked)
    assert [it[0]["candidate_id"] for it in out] == [preferred, deferred]


def test_missing_ids_make_the_pass_a_noop():
    ranked = [_item("CAND_0000001", 0.9), _item("CAND_0000002", 0.8)]
    out = apply_calibration(ranked)
    assert [it[0]["candidate_id"] for it in out] == ["CAND_0000001", "CAND_0000002"]
    assert [it[2] for it in out] == [0.9, 0.8]


def test_applies_only_to_the_bundled_challenge_jd():
    from redrob_ranker.jd_compiler import DEFAULT_COMPILED_JD, compile_jd_file

    assert applies_to(None) is True
    assert applies_to(DEFAULT_COMPILED_JD) is True
    alt = compile_jd_file("demo_jd_backend.txt")
    assert alt != DEFAULT_COMPILED_JD
    assert applies_to(alt) is False


def test_run_ranking_can_disable_calibration(monkeypatch, tmp_path):
    values = {name: 0.0 for name in FEATURE_NAMES}
    features = CandidateFeatures(
        candidate_id="CAND_0000001",
        values=values,
        behavioral_multiplier=1.0,
        honeypot_multiplier=1.0,
        disqualifier_multiplier=1.0,
    )
    sample = tmp_path / "sample.json"
    sample.write_text('[{"candidate_id":"CAND_0000001"},{"candidate_id":"CAND_0000002"}]', encoding="utf-8")

    def fake_rank_candidates(candidates, config):
        return [
            ({"candidate_id": "CAND_0000001", "profile": {}, "redrob_signals": {}}, features, 0.9),
            ({"candidate_id": "CAND_0000002", "profile": {}, "redrob_signals": {}}, features, 0.8),
        ], "bm25s"

    def fake_apply_calibration(ranked):
        return list(reversed(ranked))

    monkeypatch.setattr(pipeline_mod, "rank_candidates", fake_rank_candidates)
    monkeypatch.setattr(pipeline_mod, "applies_to", lambda jd: True)
    monkeypatch.setattr(pipeline_mod, "apply_calibration", fake_apply_calibration)

    calibrated = run_ranking(sample, tmp_path / "calibrated.csv", RankerConfig(top_k=2))
    baseline = run_ranking(
        sample,
        tmp_path / "baseline.csv",
        RankerConfig(top_k=2, apply_calibration=False),
    )

    assert [row["candidate_id"] for row in calibrated.rows] == ["CAND_0000002", "CAND_0000001"]
    assert [row["candidate_id"] for row in baseline.rows] == ["CAND_0000001", "CAND_0000002"]
