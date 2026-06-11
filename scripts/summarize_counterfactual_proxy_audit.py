"""Summarize counterfactual proxy audit CSV output."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


def percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    idx = round((pct / 100.0) * (len(sorted_values) - 1))
    idx = max(0, min(len(sorted_values) - 1, idx))
    return sorted_values[idx]


def summarize(path: Path) -> dict[str, dict[str, float | int]]:
    by_variant: dict[str, list[float]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            by_variant.setdefault(row["variant"], []).append(float(row["score_delta"]))

    summary: dict[str, dict[str, float | int]] = {}
    for variant, values in sorted(by_variant.items()):
        ordered = sorted(values)
        summary[variant] = {
            "n": len(values),
            "nonzero": sum(1 for value in values if abs(value) > 1e-9),
            "positive": sum(1 for value in values if value > 1e-9),
            "negative": sum(1 for value in values if value < -1e-9),
            "mean": round(statistics.mean(values), 6) if values else 0.0,
            "median": round(statistics.median(values), 6) if values else 0.0,
            "p05": round(percentile(ordered, 5), 6),
            "p95": round(percentile(ordered, 95), 6),
            "min": round(min(values), 6) if values else 0.0,
            "max": round(max(values), 6) if values else 0.0,
            "max_abs": round(max(abs(value) for value in values), 6) if values else 0.0,
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a counterfactual proxy audit CSV.")
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    summary = summarize(args.audit)
    payload = json.dumps(summary, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
