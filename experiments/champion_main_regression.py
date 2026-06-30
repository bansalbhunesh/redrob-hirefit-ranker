"""Exhaustive frozen-artifact regression: champion versus main.

Evaluates both explicit unlabeled policies across every available label family
and every component metric. The script fails if the champion loses any
composite, while still reporting component-level tradeoffs instead of hiding
them inside an average.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from experiments.public_field_benchmark import _label_sets  # noqa: E402
from redrob_ranker.eval import dcg  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels, load_submission  # noqa: E402
from redrob_ranker.eval_harness import RELEVANT_TIER  # noqa: E402

EXTRA_LABELS = (
    "merged_j1",
    "merged_j2",
    "merged_j3",
    "relabel_j4",
    "relabel_g25",
    "blind_test_frozen",
)
METRICS = ("ndcg10", "ndcg50", "map", "p10", "composite")
BASE_LABEL_PATHS = (
    "artifacts/h2_availblind_labels.jsonl",
    "artifacts/independent_labels_100k.jsonl",
    "docs/llm_judge_eval_labels.jsonl",
    "docs/llm_judge_eval_2_labels.jsonl",
    "docs/llm_judge_eval_3_labels.jsonl",
    "artifacts/llm_labels_expand.jsonl",
    "artifacts/silver_labels_20k.jsonl",
)


class FastEvaluator:
    """Precompute label-wide constants for repeated order evaluation."""

    def __init__(self, labels):
        self.gains = labels.gains
        self.tiers = labels.tiers
        ideal = sorted(self.gains.values(), reverse=True)
        self.ideal10 = dcg(ideal[:10], 10)
        self.ideal50 = dcg(ideal[:50], 50)
        self.relevant = sum(value >= RELEVANT_TIER for value in self.tiers.values())

    def score(self, ids: tuple[str, ...], policy: str) -> tuple[float, ...]:
        ranked = (
            [cid for cid in ids if cid in self.tiers]
            if policy == "exclude"
            else list(ids)
        )
        gains = [self.gains.get(cid, 0.0) for cid in ranked]
        ndcg10 = dcg(gains[:10], 10) / self.ideal10 if self.ideal10 else 0.0
        ndcg50 = dcg(gains[:50], 50) / self.ideal50 if self.ideal50 else 0.0
        hits = 0
        precision_sum = 0.0
        for rank, cid in enumerate(ranked, 1):
            if self.tiers.get(cid, 0.0) >= RELEVANT_TIER:
                hits += 1
                precision_sum += hits / rank
        denominator = min(self.relevant, len(ranked)) if ranked else self.relevant
        mean_ap = precision_sum / denominator if denominator else 0.0
        p10 = (
            sum(
                self.tiers.get(cid, 0.0) >= RELEVANT_TIER
                for cid in ranked[:10]
            )
            / 10
            if ranked
            else 0.0
        )
        composite = 0.5 * ndcg10 + 0.3 * ndcg50 + 0.15 * mean_ap + 0.05 * p10
        return ndcg10, ndcg50, mean_ap, p10, composite


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _status(delta: float, tolerance: float = 1e-12) -> str:
    if delta > tolerance:
        return "win"
    if delta < -tolerance:
        return "loss"
    return "tie"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--champion", type=Path, required=True)
    parser.add_argument("--labels-root", type=Path, required=True)
    parser.add_argument("--reviewer-csv", type=Path, required=True)
    parser.add_argument("--extra-labels-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--strict-all-components",
        action="store_true",
        help="Also fail on any NDCG/MAP/P@10 loss; normally composites are the ship gate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    main_ids = load_submission(args.main)
    champion_ids = load_submission(args.champion)
    names, label_sets = _label_sets(args.labels_root, args.reviewer_csv)
    names += list(EXTRA_LABELS)
    label_sets += [
        load_labels(args.extra_labels_root / f"{name}.jsonl", name)
        for name in EXTRA_LABELS
    ]
    source_paths = (
        [args.labels_root / path for path in BASE_LABEL_PATHS]
        + [args.reviewer_csv, args.reviewer_csv]
        + [args.extra_labels_root / f"{name}.jsonl" for name in EXTRA_LABELS]
    )

    comparisons = []
    counts = {
        policy: {metric: {"wins": 0, "ties": 0, "losses": 0} for metric in METRICS}
        for policy in ("exclude", "zero")
    }
    losses = []
    for policy in ("exclude", "zero"):
        for name, labels in zip(names, label_sets, strict=True):
            baseline = evaluate(main_ids, labels, unlabeled=policy)
            champion = evaluate(champion_ids, labels, unlabeled=policy)
            cells = {}
            for metric in METRICS:
                baseline_value = float(getattr(baseline, metric))
                champion_value = float(getattr(champion, metric))
                delta = champion_value - baseline_value
                status = _status(delta)
                bucket = {"win": "wins", "tie": "ties", "loss": "losses"}[status]
                counts[policy][metric][bucket] += 1
                cell = {
                    "main": baseline_value,
                    "champion": champion_value,
                    "delta": delta,
                    "status": status,
                }
                cells[metric] = cell
                if status == "loss":
                    losses.append({"policy": policy, "label": name, "metric": metric, **cell})
            comparisons.append(
                {
                    "policy": policy,
                    "label": name,
                    "main": asdict(baseline),
                    "champion": asdict(champion),
                    "cells": cells,
                }
            )

    changed_positions = sum(
        left != right for left, right in zip(main_ids, champion_ids, strict=True)
    )
    report = {
        "schema_version": 1,
        "main": {"sha256": _sha256(args.main), "rows": len(main_ids)},
        "champion": {"sha256": _sha256(args.champion), "rows": len(champion_ids)},
        "ordering": {
            "changed_positions": changed_positions,
            "membership_overlap": len(set(main_ids) & set(champion_ids)),
            "main_only": sorted(set(main_ids) - set(champion_ids)),
            "champion_only": sorted(set(champion_ids) - set(main_ids)),
        },
        "label_families": names,
        "label_sources": {
            name: {"sha256": _sha256(path), "bytes": path.stat().st_size}
            for name, path in zip(names, source_paths, strict=True)
        },
        "policies": ["exclude", "zero"],
        "counts": counts,
        "losses": losses,
        "comparisons": comparisons,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    composite_losses = sum(
        counts[policy]["composite"]["losses"] for policy in ("exclude", "zero")
    )
    component_losses = sum(
        counts[policy][metric]["losses"]
        for policy in ("exclude", "zero")
        for metric in METRICS[:-1]
    )
    print(
        f"labels={len(names)} policies=2 cells={len(names) * len(METRICS) * 2} "
        f"composite_losses={composite_losses} component_losses={component_losses}"
    )
    print(json.dumps(counts, indent=2))
    if composite_losses:
        raise SystemExit("Champion regresses on at least one composite")
    if args.strict_all_components and component_losses:
        raise SystemExit("Champion regresses on at least one component metric")


if __name__ == "__main__":
    main()
