"""Consensus calibration pass: semantics and safety gates."""

from redrob_ranker.calibration import (
    CALIBRATION_PREFERENCES,
    applies_to,
    apply_calibration,
)


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
