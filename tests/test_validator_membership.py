"""Candidate-membership validation: a submission ID must exist in the pool.

A syntactically valid but nonexistent ID (e.g. CAND_9999999) passes the shape
checks; the membership check rejects it when the candidate pool is provided.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.validation import validate_membership, validate_rows  # noqa: E402

POOL_IDS = {"CAND_0000001", "CAND_0000002", "CAND_0000003"}


def _row(cid: str, rank: int, score: float) -> dict:
    return {"candidate_id": cid, "rank": str(rank), "score": str(score), "reasoning": "r"}


def test_membership_accepts_ids_present_in_pool():
    rows = [_row("CAND_0000001", 1, 0.9), _row("CAND_0000002", 2, 0.8)]
    assert validate_membership(rows, POOL_IDS) == []


def test_membership_rejects_nonexistent_id():
    # CAND_9999999 matches the ID regex (shape-valid) but is not in the pool.
    rows = [_row("CAND_0000001", 1, 0.9), _row("CAND_9999999", 2, 0.8)]
    shape_errors = validate_rows(rows, expected=2)
    assert shape_errors == []  # shape checks alone cannot catch it
    errors = validate_membership(rows, POOL_IDS)
    assert errors == ["candidate_id not present in candidate pool: CAND_9999999"]


def test_validator_script_rejects_unknown_id_with_candidates_flag(tmp_path: Path):
    pool = tmp_path / "pool.jsonl"
    pool.write_text(
        "\n".join(json.dumps({"candidate_id": cid}) for cid in sorted(POOL_IDS)) + "\n",
        encoding="utf-8",
    )
    submission = tmp_path / "submission.csv"
    submission.write_text(
        "candidate_id,rank,score,reasoning\n"
        "CAND_0000001,1,0.9,r\n"
        "CAND_9999999,2,0.8,r\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_submission.py"),
            str(submission),
            "--expected",
            "2",
            "--candidates",
            str(pool),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert "CAND_9999999" in completed.stdout

    # Without the flag, the same file passes shape checks (membership not enforced).
    completed_no_flag = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_submission.py"),
            str(submission),
            "--expected",
            "2",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed_no_flag.returncode == 0
