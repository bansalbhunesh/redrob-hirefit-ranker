#!/usr/bin/env python3
"""Compare two ranked top-100 CSV files and report rank movement."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def load_ranked(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["candidate_id"]: row for row in rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare baseline and candidate ranked CSV outputs.")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--top-n", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline = load_ranked(args.baseline)
    candidate = load_ranked(args.candidate)

    baseline_ids = set(baseline)
    candidate_ids = set(candidate)
    entered = sorted(candidate_ids - baseline_ids, key=lambda cid: int(candidate[cid]["rank"]))
    left = sorted(baseline_ids - candidate_ids, key=lambda cid: int(baseline[cid]["rank"]))

    print("=== Top-100 Diff ===")
    print(f"Baseline: {args.baseline}")
    print(f"Candidate: {args.candidate}")
    print(f"Entered top 100: {len(entered)}")
    for cid in entered[:25]:
        print(f"  + {cid} -> rank {candidate[cid]['rank']} score {candidate[cid]['score']}")
    print(f"Left top 100: {len(left)}")
    for cid in left[:25]:
        print(f"  - {cid} was rank {baseline[cid]['rank']} score {baseline[cid]['score']}")

    print(f"\n=== Previous Top-{args.top_n} Movement ===")
    previous_top = sorted(baseline.values(), key=lambda row: int(row["rank"]))[: args.top_n]
    for row in previous_top:
        cid = row["candidate_id"]
        old_rank = int(row["rank"])
        if cid not in candidate:
            print(f"{cid}: {old_rank} -> OUT")
            continue
        new_rank = int(candidate[cid]["rank"])
        delta = new_rank - old_rank
        sign = "+" if delta > 0 else ""
        print(f"{cid}: {old_rank} -> {new_rank} ({sign}{delta})")


if __name__ == "__main__":
    main()
