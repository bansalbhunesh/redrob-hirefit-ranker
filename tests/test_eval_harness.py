"""Tests for the shared evaluation harness (Phase 1.1)."""

from __future__ import annotations

import math

import pytest

from redrob_ranker.eval_harness import (
    COMPOSITE_WEIGHTS,
    LabelSet,
    evaluate,
    evaluate_many,
    merge_label_sets,
)


def _labels(d: dict[str, float], name: str = "test") -> LabelSet:
    return LabelSet(name=name, tiers=dict(d), gains=dict(d))


def test_composite_weights_match_challenge_spec():
    assert COMPOSITE_WEIGHTS == {"ndcg10": 0.50, "ndcg50": 0.30, "map": 0.15, "p10": 0.05}
    assert math.isclose(sum(COMPOSITE_WEIGHTS.values()), 1.0)


def test_perfect_ranking_scores_one():
    labels = _labels({f"C{i}": float(5 - min(i, 5)) for i in range(20)})
    ranked = [f"C{i}" for i in range(20)]
    r = evaluate(ranked, labels, unlabeled="exclude")
    assert math.isclose(r.ndcg10, 1.0)
    assert r.coverage == 1.0
    assert math.isclose(r.composite, r.ndcg10 * 0.5 + r.ndcg50 * 0.3 + r.map * 0.15 + r.p10 * 0.05)


def test_exclude_policy_drops_unlabeled_and_reports_coverage():
    labels = _labels({"A": 5.0, "B": 4.0, "C": 3.0})
    ranked = ["A", "X", "B", "Y", "C"]  # X, Y unlabeled
    r = evaluate(ranked, labels, unlabeled="exclude")
    assert r.coverage == pytest.approx(3 / 5)
    assert r.n_ranked_scored == 3
    # After exclusion the ranking is A,B,C = perfect
    assert math.isclose(r.ndcg10, 1.0)
    assert math.isclose(r.p10, 3 / 10)  # only 3 labeled in window of 10


def test_zero_policy_counts_unlabeled_as_irrelevant():
    labels = _labels({"A": 5.0, "B": 4.0, "C": 3.0})
    ranked = ["A", "X", "B", "Y", "C"]
    r = evaluate(ranked, labels, unlabeled="zero")
    assert r.n_ranked_scored == 5
    assert r.ndcg10 < 1.0  # gaps hurt under zero policy


def test_unknown_policy_raises():
    labels = _labels({"A": 5.0})
    with pytest.raises(ValueError):
        evaluate(["A"], labels, unlabeled="tier0")


def test_evaluate_many_mean_composite():
    ls1 = _labels({"A": 5.0, "B": 0.0}, name="one")
    ls2 = _labels({"A": 0.0, "B": 5.0}, name="two")
    results, mean_c = evaluate_many(["A", "B"], [ls1, ls2], unlabeled="exclude")
    assert len(results) == 2
    assert math.isclose(mean_c, (results[0].composite + results[1].composite) / 2)


def test_merge_label_sets_overlay_wins():
    base = _labels({"A": 1.0, "B": 2.0}, name="base")
    extra = _labels({"B": 5.0, "C": 4.0}, name="extra")
    merged = merge_label_sets(base, extra)
    assert merged.tiers == {"A": 1.0, "B": 5.0, "C": 4.0}


def test_map_binary_at_tier_three():
    labels = _labels({"A": 3.0, "B": 2.9, "C": 5.0})
    ranked = ["B", "A", "C"]  # relevant: A, C (tier>=3)
    r = evaluate(ranked, labels, unlabeled="exclude")
    # AP = (1/2 + 2/3) / 2
    assert r.map == pytest.approx((1 / 2 + 2 / 3) / 2)
