#!/usr/bin/env python3
"""Repo-local submission validator for repeatable shape checks."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.validation import validate_rows  # noqa: E402


EXPECTED_HEADER = ["candidate_id", "rank", "score", "reasoning"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Redrob submission CSV.")
    parser.add_argument("submission", type=Path, help="Path to submission.csv")
    parser.add_argument("--expected", type=int, default=100, help="Expected number of rows")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with open(args.submission, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        header = reader.fieldnames or []

    errors: list[str] = []
    if header != EXPECTED_HEADER:
        errors.append(f"Expected header {EXPECTED_HEADER}, found {header}.")
    errors.extend(validate_rows(rows, expected=args.expected))

    if errors:
        print("Submission validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Submission is valid.")


if __name__ == "__main__":
    main()
