#!/usr/bin/env python3
"""Evaluate a ranked CSV against external ground truth labels."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.eval import ranking_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate ranked CSV against external ground truth labels.")
    parser.add_argument("--submission", required=True, type=Path, help="The submission CSV to evaluate")
    parser.add_argument("--labels", required=True, type=Path, help="JSONL file with external ground truth labels")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.submission.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = sorted(csv.DictReader(handle), key=lambda row: int(row["rank"]))
    ranked_ids = [row["candidate_id"] for row in rows]

    labels_by_id: dict[str, float] = {}
    with args.labels.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            # Expecting 'label' or 'silver_label' for compatibility
            label = float(item.get("label", item.get("silver_label", 0)))
            labels_by_id[item["candidate_id"]] = label

    report = ranking_report(ranked_ids, labels_by_id)
    print("\n=== External Evaluation Report ===")
    for key, value in report.items():
        print(f"{key}: {value:.4f}")
    print("==================================\n")


if __name__ == "__main__":
    main()
