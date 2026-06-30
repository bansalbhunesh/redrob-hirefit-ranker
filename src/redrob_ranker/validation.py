"""Submission shape validation."""

from __future__ import annotations

import math
import re

CANDIDATE_ID_PATTERN = re.compile(r"^CAND_[0-9]{7}$")


def validate_rows(rows: list[dict], expected: int = 100) -> list[str]:
    errors: list[str] = []
    if len(rows) != expected:
        errors.append(f"Expected {expected} rows, found {len(rows)}.")
    ids = set()
    ranks = set()
    last_score = float("inf")
    last_cid = ""
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
        finite_score = math.isfinite(score)
        if not finite_score:
            errors.append(f"Score is not finite at rank {rank}: {score}")
        elif score < 0 or score > 1:
            errors.append(f"Score out of range at rank {rank}: {score}")
        if rank < 1 or rank > expected:
            errors.append(f"Rank out of range: {rank}")
        if finite_score and score > last_score:
            errors.append(f"Score increases at rank {rank}.")
        # Mirror the official validator's tie-break rule: when two consecutive rows
        # share the same score, candidate_id must be ascending. Two distinct raw
        # scores can round to the same 6-decimal submission score, so guard it here
        # to ensure we never ship a CSV the official validator would auto-reject.
        if finite_score and score == last_score and cid < last_cid:
            errors.append(
                f"Equal scores at rank {rank}: tie-break requires candidate_id "
                f"ascending ({last_cid} > {cid})."
            )
        if finite_score:
            last_score = score
        last_cid = cid
        if not str(row.get("reasoning", "")).strip():
            errors.append(f"Missing reasoning at rank {rank}.")
    missing = set(range(1, expected + 1)) - ranks
    if missing:
        errors.append(f"Missing ranks: {sorted(missing)}")
    return errors


def validate_membership(rows: list[dict], known_ids: set[str]) -> list[str]:
    """Reject syntactically valid candidate_ids that do not exist in the pool."""
    return [
        f"candidate_id not present in candidate pool: {row.get('candidate_id')}"
        for row in rows
        if str(row.get("candidate_id", "")) not in known_ids
    ]
