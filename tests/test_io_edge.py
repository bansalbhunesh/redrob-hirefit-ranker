"""Edge-case coverage: candidate IO formats, CSV round-trips, CLI paths."""

from __future__ import annotations

import csv
import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from redrob_ranker.features import compute_features
from redrob_ranker.io import iter_candidates, write_submission
from redrob_ranker.validation import validate_rows

ROOT = Path(__file__).resolve().parents[1]

MINIMAL = {
    "candidate_id": "CAND_0000001",
    "profile": {"current_title": "ML Engineer", "years_of_experience": 6},
    "career_history": [],
    "education": [],
    "skills": [],
    "redrob_signals": {},
}


def test_iter_candidates_jsonl_gz(tmp_path: Path):
    path = tmp_path / "c.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(json.dumps(MINIMAL) + "\n\n")  # incl. a blank line
    out = list(iter_candidates(path))
    assert len(out) == 1
    assert out[0]["candidate_id"] == "CAND_0000001"


def test_iter_candidates_bom_jsonl(tmp_path: Path):
    path = tmp_path / "c.jsonl"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(MINIMAL).encode("utf-8") + b"\n")
    out = list(iter_candidates(path))
    assert out[0]["candidate_id"] == "CAND_0000001"


def test_iter_candidates_missing_id_gets_placeholder(tmp_path: Path):
    path = tmp_path / "c.jsonl"
    rec = dict(MINIMAL)
    rec.pop("candidate_id")
    path.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    out = list(iter_candidates(path))
    assert out[0]["candidate_id"] == "UNKNOWN_ROW_0"


def test_iter_candidates_json_array_and_cap(tmp_path: Path):
    path = tmp_path / "c.json"
    recs = []
    for i in range(5):
        r = dict(MINIMAL)
        r["candidate_id"] = f"CAND_{i:07d}"
        recs.append(r)
    path.write_text(json.dumps(recs), encoding="utf-8")
    out = list(iter_candidates(path, max_candidates=3))
    assert [c["candidate_id"] for c in out] == ["CAND_0000000", "CAND_0000001", "CAND_0000002"]


def test_write_submission_unicode_and_quoting_roundtrip(tmp_path: Path):
    rows = [{
        "candidate_id": "CAND_0000001",
        "rank": 1,
        "score": "1.000000",
        "reasoning": 'Said "hands-on, scrappy"; café-grade UTF-8 ✓, commas, and\nnewlines survive CSV quoting.',
    }]
    out = tmp_path / "s.csv"
    write_submission(out, rows)
    back = list(csv.DictReader(open(out, encoding="utf-8", newline="")))
    assert back[0]["reasoning"] == rows[0]["reasoning"]


def test_write_submission_failure_preserves_existing_file(tmp_path: Path):
    out = tmp_path / "submission.csv"
    out.write_text("known-good\n", encoding="utf-8")

    def broken_rows():
        yield {
            "candidate_id": "CAND_0000001",
            "rank": 1,
            "score": "1.000000",
            "reasoning": "valid first row",
        }
        raise RuntimeError("simulated write failure")

    with pytest.raises(RuntimeError, match="simulated write failure"):
        write_submission(out, broken_rows())

    assert out.read_text(encoding="utf-8") == "known-good\n"
    assert list(tmp_path.glob(".submission.csv.*.tmp")) == []


def test_validate_rows_catches_shape_errors():
    rows = [
        {"candidate_id": "CAND_0000001", "rank": 1, "score": "0.5", "reasoning": "a"},
        {"candidate_id": "CAND_0000001", "rank": 1, "score": "0.9", "reasoning": "b"},
        {"candidate_id": "bad-id", "rank": 3, "score": "2.0", "reasoning": "c"},
    ]
    errors = validate_rows(rows, expected=3)
    blob = " ".join(errors)
    assert "Duplicate candidate_id" in blob
    assert "Duplicate rank" in blob
    assert "Invalid candidate_id" in blob
    assert "out of range" in blob
    assert "increases" in blob  # 0.5 -> 0.9 ordering violation


def test_compute_features_minimal_and_hostile_dicts():
    # minimal but well-formed
    feats = compute_features(dict(MINIMAL))
    assert feats.honeypot_multiplier == 1.0
    assert 0.0 <= feats.behavioral_multiplier <= 1.10
    # hostile shapes must not raise
    for hostile in (
        {"candidate_id": "CAND_0000002"},
        {"candidate_id": "CAND_0000003", "profile": {}, "skills": None,
         "career_history": None, "education": None, "redrob_signals": None},
        {"candidate_id": "CAND_0000004", "profile": {"years_of_experience": "7"},
         "skills": [{"name": None, "proficiency": None}],
         "career_history": [{"company": None, "duration_months": None}],
         "redrob_signals": {"notice_period_days": None}},
    ):
        f = compute_features(hostile)
        assert f.candidate_id.startswith("CAND_")


def test_eval_harness_cli_smoke(tmp_path: Path):
    sub = tmp_path / "s.csv"
    sub.write_text(
        "candidate_id,rank,score,reasoning\nCAND_0000001,1,1.000000,ok\nCAND_0000002,2,0.5,ok\n",
        encoding="utf-8",
    )
    labels = tmp_path / "l.jsonl"
    labels.write_text(
        '{"candidate_id": "CAND_0000001", "tier": 5}\n{"candidate_id": "CAND_0000002", "tier": 0}\n',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        [sys.executable, "-m", "redrob_ranker.eval_harness",
         "--submission", str(sub), "--labels", str(labels)],
        text=True, capture_output=True, env=env, timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    assert "composite=" in completed.stdout
    assert "coverage=100.0%" in completed.stdout


def test_rank_cli_with_demo_jd(tmp_path: Path):
    sample = tmp_path / "sample.jsonl"
    rec = {
        "candidate_id": "CAND_0000001",
        "profile": {"current_title": "Senior Backend Engineer", "summary": "REST APIs on Kafka",
                    "location": "Chennai", "country": "India", "years_of_experience": 6,
                    "current_company": "Acme"},
        "career_history": [{"company": "Acme", "title": "Backend Engineer", "duration_months": 60,
                            "description": "Built REST APIs on Kafka and Spark in production"}],
        "education": [], "skills": [
            {"name": "Python", "proficiency": "advanced", "endorsements": 10, "duration_months": 48}],
        "redrob_signals": {"open_to_work_flag": True, "recruiter_response_rate": 0.7,
                           "notice_period_days": 30, "last_active_date": "2026-05-20"},
    }
    sample.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    out = tmp_path / "out.csv"
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, "rank.py", "--candidates", str(sample), "--out", str(out),
         "--top-k", "1", "--bm25-backend", "bm25s", "--jd", "demo_jd_backend.txt"],
        cwd=ROOT, text=True, capture_output=True, env=env, timeout=180,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Compiled demo_jd_backend.txt" in completed.stderr
    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    assert rows[0]["candidate_id"] == "CAND_0000001"
