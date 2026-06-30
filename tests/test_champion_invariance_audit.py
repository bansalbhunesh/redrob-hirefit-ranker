import json
from pathlib import Path

from experiments.champion_main_regression import METRICS, FastEvaluator
from redrob_ranker.eval_harness import LabelSet, evaluate


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    return json.loads((ROOT / "experiments" / name).read_text(encoding="utf-8"))


def test_champion_beats_main_on_every_composite_under_both_policies():
    report = _load("champion_main_exhaustive_results.json")

    assert report["main"]["sha256"] == (
        "24f84f4b6160a4bcb164369c7f6ab27a060953ec7cfc0d33ed4849eab1194aea"
    )
    assert report["champion"]["sha256"] == (
        "8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062"
    )
    assert len(report["label_families"]) == 15
    assert report["label_sources"]["reviewer"]["sha256"] == (
        "68764999a03aba32659cf02aad4b6e8214e897449c508d4a4bcad6ae5ab50b47"
    )
    assert report["label_sources"]["blind"] == report["label_sources"]["reviewer"]
    for policy in ("exclude", "zero"):
        assert report["counts"][policy]["composite"] == {
            "wins": 15,
            "ties": 0,
            "losses": 0,
        }
    assert len(report["losses"]) == 6


def test_no_simple_fusion_closes_components_without_losing_champion():
    fusion = _load("main_champion_safety_fusion_results.json")
    audit = _load("champion_invariance_audit_2026-06-30.json")

    assert fusion["variant_count"] == 883
    assert fusion["main_safe_count"] == 12
    assert fusion["fully_safe_count"] == 0
    assert audit["artifacts"]["origin_main_profile_sha256"] == audit["artifacts"][
        "v6_main_profile_sha256"
    ]
    assert audit["docker"]["low_memory_failure"]["preexisting_output_preserved"]
    assert audit["supply_chain"]["pip_require_hashes"]


def test_fast_repeated_evaluator_matches_canonical_harness():
    labels = LabelSet(
        "synthetic",
        tiers={"CAND_0000001": 4.0, "CAND_0000002": 2.0, "CAND_0000003": 0.0},
        gains={"CAND_0000001": 4.0, "CAND_0000002": 2.0, "CAND_0000003": 0.0},
    )
    order = ("CAND_0000002", "CAND_0000004", "CAND_0000001", "CAND_0000003")
    evaluator = FastEvaluator(labels)

    for policy in ("exclude", "zero"):
        result = evaluate(list(order), labels, unlabeled=policy)
        expected = tuple(float(getattr(result, metric)) for metric in METRICS)
        assert evaluator.score(order, policy) == expected
