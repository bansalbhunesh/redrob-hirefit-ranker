"""Search simple, auditable main/champion safety fusions.

This is a diagnostic, not an automatic promotion path. It asks whether any
small rank-space fusion can match main on every measured component while also
retaining the champion's composite gains.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from experiments.champion_main_regression import (  # noqa: E402
    EXTRA_LABELS,
    METRICS,
    FastEvaluator,
)
from experiments.public_field_benchmark import _label_sets  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels, load_submission  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--champion", type=Path, required=True)
    parser.add_argument("--labels-root", type=Path, required=True)
    parser.add_argument("--reviewer-csv", type=Path, required=True)
    parser.add_argument("--extra-labels-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _prefix(prefix: list[str], tail: list[str], size: int) -> tuple[str, ...]:
    selected = list(prefix[:size])
    selected.extend(cid for cid in tail if cid not in set(selected))
    return tuple(selected[:100])


def _rrf(
    main: list[str], champion: list[str], champion_weight: float, k: float
) -> tuple[str, ...]:
    union = list(dict.fromkeys(main + champion))
    missing = len(union) + 100
    main_rank = {cid: rank for rank, cid in enumerate(main, 1)}
    champion_rank = {cid: rank for rank, cid in enumerate(champion, 1)}

    def score(cid: str) -> float:
        return (1.0 - champion_weight) / (k + main_rank.get(cid, missing)) + (
            champion_weight / (k + champion_rank.get(cid, missing))
        )

    return tuple(sorted(union, key=lambda cid: (-score(cid), cid))[:100])


def _linear(
    main: list[str], champion: list[str], champion_weight: float
) -> tuple[str, ...]:
    union = list(dict.fromkeys(main + champion))
    missing = len(union) + 100
    main_rank = {cid: rank for rank, cid in enumerate(main, 1)}
    champion_rank = {cid: rank for rank, cid in enumerate(champion, 1)}
    return tuple(
        sorted(
            union,
            key=lambda cid: (
                (1.0 - champion_weight) * main_rank.get(cid, missing)
                + champion_weight * champion_rank.get(cid, missing),
                cid,
            ),
        )[:100]
    )


def _main_order_band(
    champion: list[str], main: list[str], start: int, stop: int
) -> tuple[str, ...]:
    main_rank = {cid: rank for rank, cid in enumerate(main, 1)}
    result = list(champion)
    result[start:stop] = sorted(
        result[start:stop], key=lambda cid: (main_rank.get(cid, 10_000), cid)
    )
    return tuple(result)


def _vector(order: tuple[str, ...], evaluators) -> np.ndarray:
    values = []
    for policy in ("exclude", "zero"):
        for evaluator in evaluators:
            values.extend(evaluator.score(order, policy))
    return np.asarray(values, dtype=np.float64)


def _summary(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "order"}


def main() -> None:
    args = parse_args()
    main_order = load_submission(args.main)
    champion_order = load_submission(args.champion)
    names, label_sets = _label_sets(args.labels_root, args.reviewer_csv)
    names += list(EXTRA_LABELS)
    label_sets += [
        load_labels(args.extra_labels_root / f"{name}.jsonl", name)
        for name in EXTRA_LABELS
    ]
    evaluators = [FastEvaluator(labels) for labels in label_sets]
    for order in (tuple(main_order), tuple(champion_order)):
        for policy in ("exclude", "zero"):
            for labels, evaluator in zip(label_sets, evaluators, strict=True):
                canonical = evaluate(list(order), labels, unlabeled=policy)
                expected = tuple(float(getattr(canonical, metric)) for metric in METRICS)
                actual = evaluator.score(order, policy)
                if not np.allclose(actual, expected, rtol=0.0, atol=1e-15):
                    raise RuntimeError(
                        f"Fast evaluator drift for {labels.name}/{policy}: "
                        f"{actual} != {expected}"
                    )
    main_vector = _vector(tuple(main_order), evaluators)
    champion_vector = _vector(tuple(champion_order), evaluators)
    composite_indices = np.asarray(
        [index for index in range(len(main_vector)) if index % len(METRICS) == 4]
    )
    component_indices = np.asarray(
        [index for index in range(len(main_vector)) if index % len(METRICS) != 4]
    )

    variants: dict[tuple[str, ...], dict] = {
        tuple(main_order): {"kind": "main"},
        tuple(champion_order): {"kind": "champion"},
    }
    for size in range(1, 101):
        variants.setdefault(
            _prefix(main_order, champion_order, size),
            {"kind": "main_prefix", "size": size},
        )
        variants.setdefault(
            _prefix(champion_order, main_order, size),
            {"kind": "champion_prefix", "size": size},
        )
    for weight in np.linspace(0.0, 1.0, 101):
        for k in (0.0, 10.0, 50.0, 100.0):
            variants.setdefault(
                _rrf(main_order, champion_order, float(weight), k),
                {"kind": "rrf", "champion_weight": float(weight), "k": k},
            )
        variants.setdefault(
            _linear(main_order, champion_order, float(weight)),
            {"kind": "linear", "champion_weight": float(weight)},
        )
    for start in range(0, 100, 5):
        for stop in range(start + 5, 101, 5):
            variants.setdefault(
                _main_order_band(champion_order, main_order, start, stop),
                {"kind": "main_order_band", "start": start + 1, "stop": stop},
            )

    rows = []
    for order, params in variants.items():
        vector = _vector(order, evaluators)
        main_delta = vector - main_vector
        champion_delta = vector - champion_vector
        rows.append(
            {
                "params": params,
                "main_component_losses": int(
                    np.sum(main_delta[component_indices] < -1e-12)
                ),
                "main_composite_losses": int(
                    np.sum(main_delta[composite_indices] < -1e-12)
                ),
                "champion_composite_losses": int(
                    np.sum(champion_delta[composite_indices] < -1e-12)
                ),
                "mean_composite": float(vector[composite_indices].mean()),
                "min_main_delta": float(main_delta.min()),
                "changed_from_champion": sum(
                    left != right
                    for left, right in zip(order, champion_order, strict=True)
                ),
                "order": list(order),
            }
        )

    main_safe = [
        row
        for row in rows
        if row["main_component_losses"] == 0 and row["main_composite_losses"] == 0
    ]
    fully_safe = [row for row in main_safe if row["champion_composite_losses"] == 0]
    main_safe.sort(
        key=lambda row: (
            -row["champion_composite_losses"],
            row["mean_composite"],
            -row["changed_from_champion"],
        ),
        reverse=True,
    )
    fully_safe.sort(key=lambda row: row["mean_composite"], reverse=True)
    rows.sort(
        key=lambda row: (
            -row["main_composite_losses"],
            -row["main_component_losses"],
            -row["champion_composite_losses"],
            row["mean_composite"],
        ),
        reverse=True,
    )
    report = {
        "schema_version": 1,
        "labels": names,
        "variant_count": len(variants),
        "main_safe_count": len(main_safe),
        "fully_safe_count": len(fully_safe),
        "best_main_safe": [_summary(row) for row in main_safe[:20]],
        "best_fully_safe": [_summary(row) for row in fully_safe[:20]],
        "best_tradeoffs": [_summary(row) for row in rows[:20]],
    }
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"variants={len(variants)} main_safe={len(main_safe)} "
        f"fully_safe={len(fully_safe)}"
    )
    if main_safe:
        print("best_main_safe", json.dumps(_summary(main_safe[0])))
    if fully_safe:
        print("best_fully_safe", json.dumps(_summary(fully_safe[0])))


if __name__ == "__main__":
    main()
