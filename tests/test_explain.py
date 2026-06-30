"""Faithfulness + exactness checks for the opt-in explainability module.

The decisive test is `test_reconstructs_universal_v2`: the attribution path must
reproduce the *shipped* challenger score, so the explanation is of the real
scorer and not a lookalike.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from redrob_ranker.challenger import universal_v2_score
from redrob_ranker.explain import (
    CandidateRecord,
    final_score_from_relevance,
    global_importance,
    rank_stability,
    relevance_attributions,
)
from redrob_ranker.features import compute_features
from redrob_ranker.io import iter_candidates
from redrob_ranker.retrieval import retrieve_pool

_SAMPLE = Path(__file__).resolve().parents[1] / "demo_sample.jsonl"


def _sample_records(limit: int = 60):
    candidates = list(iter_candidates(_SAMPLE))[:limit]
    retrieval_scores, _ = retrieve_pool(candidates, 0)
    records, features_by_id = [], {}
    for idx, candidate in enumerate(candidates):
        features = compute_features(candidate)
        cid = candidate["candidate_id"]
        features_by_id[cid] = (features, retrieval_scores.get(idx, 0.0))
        records.append(
            CandidateRecord(
                candidate_id=cid,
                values=dict(features.values),
                retrieval_score=retrieval_scores.get(idx, 0.0),
                behavioral_multiplier=features.behavioral_multiplier,
                honeypot_multiplier=features.honeypot_multiplier,
                disqualifier_multiplier=features.disqualifier_multiplier,
            )
        )
    return records, features_by_id


@pytest.mark.skipif(not _SAMPLE.exists(), reason="demo_sample.jsonl not present")
def test_attributions_sum_to_relevance():
    records, _ = _sample_records()
    for rec in records:
        contributions, relevance = relevance_attributions(
            rec.values, rec.retrieval_score, rec.semantic_score
        )
        assert math.isclose(sum(contributions.values()), relevance, rel_tol=0, abs_tol=1e-12)


@pytest.mark.skipif(not _SAMPLE.exists(), reason="demo_sample.jsonl not present")
def test_reconstructs_universal_v2():
    """relevance x gates must equal the shipped challenger score, exactly."""
    records, features_by_id = _sample_records()
    for rec in records:
        features, retrieval = features_by_id[rec.candidate_id]
        _, relevance = relevance_attributions(rec.values, retrieval, None)
        reconstructed = final_score_from_relevance(
            relevance,
            rec.behavioral_multiplier,
            rec.honeypot_multiplier,
            rec.disqualifier_multiplier,
        )
        shipped = universal_v2_score(features, retrieval, None)
        assert math.isclose(reconstructed, shipped, rel_tol=1e-9, abs_tol=1e-12)


@pytest.mark.skipif(not _SAMPLE.exists(), reason="demo_sample.jsonl not present")
def test_rank_stability_and_importance_shapes():
    records, _ = _sample_records()
    importance = global_importance(records)
    assert importance and importance[0][1] >= importance[-1][1]  # sorted desc
    bands = rank_stability(records, top_k=10)
    assert len(bands) == min(10, len(records))
    for base_rank, lo, hi in bands.values():
        assert lo <= base_rank <= hi  # base rank inside its own ablation band
