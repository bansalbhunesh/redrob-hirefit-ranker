"""Submission shape validation."""

from __future__ import annotations

import re

CANDIDATE_ID_PATTERN = re.compile(r"^CAND_[0-9]{7}$")


def validate_rows(rows: list[dict], expected: int = 100) -> list[str]:
    errors: list[str] = []
    if len(rows) != expected:
        errors.append(f"Expected {expected} rows, found {len(rows)}.")
    ids = set()
    ranks = set()
    last_score = float("inf")
    for row in rows:
        cid = str(row.get("candidate_id", ""))
        try:
            rank = int(row.get("rank", 0))
        except (TypeError, ValueError):
            rank = 0
        try:
            score = float(row.get("score", 0))
        except (TypeError, ValueError):
            score = -1.0
        if not CANDIDATE_ID_PATTERN.match(cid):
            errors.append(f"Invalid candidate_id: {cid}")
        if cid in ids:
            errors.append(f"Duplicate candidate_id: {cid}")
        ids.add(cid)
        if rank in ranks:
            errors.append(f"Duplicate rank: {rank}")
        ranks.add(rank)
        if score < 0 or score > 1:
            errors.append(f"Score out of range at rank {rank}: {score}")
        if score > last_score:
            errors.append(f"Score increases at rank {rank}.")
        last_score = score
    missing = set(range(1, expected + 1)) - ranks
    if missing:
        errors.append(f"Missing ranks: {sorted(missing)}")
    return errors
