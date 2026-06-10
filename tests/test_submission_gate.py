"""Phase-0 merge gates: format validity + golden-output regression.

These tests pin the official artifact:
1. The committed submission.csv must always pass the format validator.
2. The committed submission.csv bytes must match the recorded golden hash
   (catches manual edits or accidental regeneration drift).
3. Re-ranking a fixed 2K slice of the official pool must reproduce a recorded
   hash byte-for-byte (catches any code change that silently alters ranking
   behavior, in seconds instead of a full 100K run).

If a ranking-behavior change is ever intentional (per the pre-registered
decision rule in docs/sensitivity_sweep.md), regenerate submission.csv and
update BOTH hashes below in the same commit, citing the measurement.
"""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission.csv"
CANDIDATES = ROOT / "candidates.jsonl"

# Golden hash of the committed full-pool submission (sha256, lowercase hex).
GOLDEN_SUBMISSION_SHA256 = "e1a696d1f575908c8544fae294e04dcbf4edd4bad8ee5215aae2072c867493f7"

# Recorded hash of rank.py output for the first 2,000 candidates of the
# official candidates.jsonl (top-100, bm25s backend, PYTHONHASHSEED=0).
GOLDEN_SLICE2K_SHA256 = "455d08d4d7fd45697e7f8ee05c00c1b13f3001bd4e2123dbda2726fd2e7d5bb1"

EXPECTED_HEADER = ["candidate_id", "rank", "score", "reasoning"]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_committed_submission_passes_validator():
    sys.path.insert(0, str(ROOT / "src"))
    from redrob_ranker.validation import validate_rows

    with SUBMISSION.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        header = reader.fieldnames or []

    assert header == EXPECTED_HEADER
    errors = validate_rows(rows, expected=100)
    assert errors == []


def test_committed_submission_matches_golden_hash():
    assert _sha256(SUBMISSION) == GOLDEN_SUBMISSION_SHA256, (
        "submission.csv no longer matches the recorded golden hash. If this "
        "change was the measured outcome of the pre-registered decision rule, "
        "update GOLDEN_SUBMISSION_SHA256 (and the slice hash) in this test; "
        "otherwise the file drifted and must be restored."
    )


@pytest.mark.skipif(not CANDIDATES.exists(), reason="official candidates.jsonl not present")
def test_fixed_slice_rerank_reproduces_recorded_hash(tmp_path: Path):
    out = tmp_path / "slice2k.csv"
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            "rank.py",
            "--candidates",
            str(CANDIDATES),
            "--out",
            str(out),
            "--max-candidates",
            "2000",
            "--bm25-backend",
            "bm25s",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr
    assert _sha256(out) == GOLDEN_SLICE2K_SHA256, (
        "Re-ranking the fixed 2K slice produced different bytes: ranking "
        "behavior changed. Either revert the change or follow the "
        "pre-registered protocol and update both golden hashes."
    )
