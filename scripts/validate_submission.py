#!/usr/bin/env python3
"""Repo-local submission validator for repeatable shape checks."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

VALIDATION_MODULE = SRC / "redrob_ranker" / "validation.py"
spec = importlib.util.spec_from_file_location("redrob_ranker_validation", VALIDATION_MODULE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load validator module from {VALIDATION_MODULE}")
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
validate_rows = validation_module.validate_rows
validate_membership = validation_module.validate_membership


EXPECTED_HEADER = ["candidate_id", "rank", "score", "reasoning"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Redrob submission CSV.")
    parser.add_argument("submission", type=Path, help="Path to submission.csv")
    parser.add_argument("--expected", type=int, default=100, help="Expected number of rows")
    parser.add_argument(
        "--candidates",
        type=Path,
        default=None,
        help="Optional candidates.jsonl[.gz]: also reject submission IDs that do "
        "not exist in the candidate pool.",
    )
    return parser.parse_args()


def load_pool_ids(path: Path) -> set[str]:
    from redrob_ranker.io import iter_candidates

    return {c["candidate_id"] for c in iter_candidates(path) if c.get("candidate_id")}


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
    if args.candidates is not None:
        errors.extend(validate_membership(rows, load_pool_ids(args.candidates)))

    if errors:
        print("Submission validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Submission is valid.")


if __name__ == "__main__":
    main()
