from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import rank
from redrob_ranker.pipeline import CHAMPION_SCORING_PROFILE

ROOT = Path(__file__).resolve().parents[1]


def _args(**overrides):
    values = {
        "scoring_profile": None,
        "top_k": 100,
        "max_candidates": None,
        "candidate_pool": 0,
        "jd": None,
        "use_embeddings": False,
        "bm25_backend": "auto",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _result(**overrides):
    values = {
        "loaded_count": 100_000,
        "ranked_pool_count": 100_000,
        "rows": [{}] * 100,
        "bm25_backend": "bm25s",
        "honeypots_detected": 53,
        "honeypots_in_output": 0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_release_forces_verified_champion(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PYTHONHASHSEED", "0")

    assert rank._release_profile(_args()) == CHAMPION_SCORING_PROFILE
    assert rank._release_profile(
        _args(scoring_profile=CHAMPION_SCORING_PROFILE)
    ) == CHAMPION_SCORING_PROFILE


@pytest.mark.parametrize(
    "overrides",
    [
        {"scoring_profile": "main"},
        {"top_k": 99},
        {"max_candidates": 99_999},
        {"candidate_pool": 3_000},
        {"jd": "job.txt"},
        {"use_embeddings": True},
        {"bm25_backend": "rank_bm25"},
    ],
)
def test_release_rejects_noncanonical_options(
    monkeypatch: pytest.MonkeyPatch, overrides
):
    monkeypatch.setenv("PYTHONHASHSEED", "0")

    with pytest.raises(SystemExit):
        rank._release_profile(_args(**overrides))


def test_release_requires_deterministic_hash_seed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PYTHONHASHSEED", raising=False)

    with pytest.raises(SystemExit, match="PYTHONHASHSEED=0"):
        rank._release_profile(_args())


def test_release_verifier_accepts_only_exact_committed_artifact():
    rank._verify_release(_result(), ROOT / "submission.csv")

    with pytest.raises(RuntimeError, match="expected 100000 candidates"):
        rank._verify_release(_result(loaded_count=99_999), ROOT / "submission.csv")


def test_release_constants_match_metrics_manifest():
    manifest = json.loads(
        (ROOT / "docs" / "metrics_manifest.json").read_text(encoding="utf-8")
    )

    assert rank.RELEASE_SHA256 == manifest["submission"]["golden_sha256"]
    assert (
        rank.RELEASE_CANDIDATES_SHA256
        == manifest["submission"]["candidate_input_sha256"]
    )
    assert rank.RELEASE_CANDIDATE_COUNT == manifest["submission"]["total_candidates"]
    assert rank.RELEASE_HONEYPOT_COUNT == manifest["submission"]["honeypots_detected"]


def test_release_cli_rejects_truncated_run_before_reading_input(tmp_path: Path):
    output = tmp_path / "must-not-exist.csv"
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    completed = subprocess.run(
        [
            sys.executable,
            "rank.py",
            "--release",
            "--candidates",
            str(tmp_path / "missing.jsonl"),
            "--out",
            str(output),
            "--max-candidates",
            "10",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode != 0
    assert "--max-candidates is forbidden" in completed.stderr
    assert not output.exists()
