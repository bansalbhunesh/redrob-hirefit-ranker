"""Scan candidate profiles for adversarial text integrity flags."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.integrity import integrity_flags
from redrob_ranker.io import iter_candidates
from redrob_ranker.text import candidate_text


def scan(candidates_path: Path, max_candidates: int | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for candidate in iter_candidates(candidates_path, max_candidates=max_candidates):
        flags = integrity_flags(candidate_text(candidate))
        if flags:
            rows.append(
                {
                    "candidate_id": str(candidate.get("candidate_id", "UNKNOWN")),
                    "flags": ",".join(flags),
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit candidate text for adversarial integrity flags.")
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-candidates", type=int, default=None)
    args = parser.parse_args()

    rows = scan(args.candidates, max_candidates=args.max_candidates)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "flags"])
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(flag for row in rows for flag in row["flags"].split(",") if flag)
    print(f"Scanned {args.max_candidates or 'all'} candidates; flagged {len(rows)} profiles; counts={dict(counts)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
