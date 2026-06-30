from __future__ import annotations

import numpy as np
import pytest

import redrob_ranker.loss_aggregate as loss_aggregate_module
from redrob_ranker.challenger import universal_v2_score
from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import CandidateFeatures
from redrob_ranker.loss_aggregate import (
    MODEL_PATH,
    _artifact,
    _feature_matrix,
    _predict_heads,
    rerank_loss_aggregate,
)
from redrob_ranker.pipeline import _init_worker, _score_one


def _features(index: int = 0) -> CandidateFeatures:
    values = {name: ((index + col) % 11) / 10 for col, name in enumerate(FEATURE_NAMES)}
    values["_main_score"] = 1.0 - index / 1000
    return CandidateFeatures(
        candidate_id=f"TEST_{index:04d}",
        values=values,
        behavioral_multiplier=0.8,
        honeypot_multiplier=1.0,
        disqualifier_multiplier=1.0,
    )


def test_model_artifact_contains_no_candidate_lookup() -> None:
    assert MODEL_PATH.exists()
    assert b"CAND_" not in MODEL_PATH.read_bytes()
    assert b"candidate_id" not in MODEL_PATH.read_bytes()


def test_model_artifact_corruption_fails_closed(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corrupted = tmp_path / "loss_aggregate_v3.npz"
    corrupted.write_bytes(MODEL_PATH.read_bytes() + b"corruption")
    _artifact.cache_clear()
    monkeypatch.setattr(loss_aggregate_module, "MODEL_PATH", corrupted)

    with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
        _artifact()

    _artifact.cache_clear()


def test_numpy_forest_predictions_are_finite() -> None:
    data = _artifact()
    matrix = np.zeros((3, len(data["feature_names"])), dtype=np.float64)
    predictions = _predict_heads(matrix, data)

    assert predictions.shape == (3, 7)
    assert np.isfinite(predictions).all()


def test_feature_matrix_preserves_artifact_order_and_derived_values() -> None:
    features = _features(3)
    pool = [({"candidate_id": "TEST_0003"}, features, 0.5)]
    names = np.asarray(
        ["hand", "behavior", "logistics", "role_fit", "ai_depth", "production_evidence"]
    )

    matrix = _feature_matrix(pool, names)

    assert matrix.tolist() == [[
        features.values["_main_score"],
        features.behavior,
        features.logistics,
        features.role_fit,
        features.ai_depth,
        features.production_evidence,
    ]]


def test_rank_hedge_preserves_v2_membership() -> None:
    ranked = []
    for index in range(130):
        candidate = {"candidate_id": f"TEST_{index:04d}"}
        ranked.append((candidate, _features(index), 1.0 - index / 1000))

    reranked = rerank_loss_aggregate(ranked)

    assert len(reranked) == len(ranked)
    assert {item[0]["candidate_id"] for item in reranked[:100]} == {
        item[0]["candidate_id"] for item in ranked[:100]
    }
    assert rerank_loss_aggregate(ranked)[:100] == reranked[:100]


def test_pipeline_v3_uses_v2_stage_one_and_records_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = {
        "candidate_id": "TEST_0001",
        "profile": {},
        "career_history": [],
        "skills": [],
        "redrob_signals": {},
    }
    monkeypatch.setattr(
        "redrob_ranker.pipeline.compute_features",
        lambda *_args, **_kwargs: _features(),
    )
    _init_worker(None, "loss-aggregate-v3")

    features, score = _score_one((candidate, 0.5, None))

    assert score == pytest.approx(universal_v2_score(features, 0.5))
    assert 0.0 <= features.values["_main_score"] <= 1.0
    assert features.total == score
    _init_worker(None, "main")
