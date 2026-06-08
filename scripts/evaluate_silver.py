#!/usr/bin/env python3
"""Evaluate a ranked CSV against heuristic silver labels."""

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
    parser = argparse.ArgumentParser(description="Evaluate ranked CSV against silver labels.")
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
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
            labels_by_id[item["candidate_id"]] = float(item["silver_label"])

    report = ranking_report(ranked_ids, labels_by_id)
    for key, value in report.items():
        print(f"{key}: {value:.4f}")


if __name__ == "__main__":
    main()
