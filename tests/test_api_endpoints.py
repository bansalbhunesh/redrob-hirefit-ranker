"""Endpoint tests for the FastAPI dashboard backend (apps/api/main.py).

Covers, for each route: happy path, not-found, and malformed input. Uses the
bundled demo_sample.jsonl so live/batch ranking runs the real pipeline on a
small pool (serial path, no process pool).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from apps.api import main  # noqa: E402
from redrob_ranker.constants import FEATURE_NAMES  # noqa: E402
from redrob_ranker.features import CandidateFeatures  # noqa: E402
from redrob_ranker.pipeline import RankingResult  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEMO_SAMPLE = ROOT / "demo_sample.jsonl"


@pytest.fixture()
def client():
    main.job_store.clear()
    main.results_store.clear()
    with TestClient(main.app) as c:
        yield c
    main.job_store.clear()
    main.results_store.clear()


def _demo_bytes(n_lines: int = 5) -> bytes:
    lines = DEMO_SAMPLE.read_bytes().splitlines()[:n_lines]
    return b"\n".join(lines) + b"\n"


# ── / and /api/health ──────────────────────────────────────────────


def test_index_serves_dashboard(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_index_falls_back_to_root_dashboard(client, monkeypatch, tmp_path):
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert b"Redrob HireFit Ranker" in resp.content


def test_health_reports_artifacts_and_sha(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["git_sha"] and body["git_sha"] != ""
    if (ROOT / ".git").exists():
        assert body["git_sha"] != "unknown"
    assert body["artifacts"]["precomputed_loaded"] is True
    assert body["artifacts"]["precomputed_bytes"] > 0
    assert body["artifacts"]["dashboard_present"] is True
    assert {"stored", "active"} <= set(body["jobs"])
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"


# ── /api/results (showpiece) ───────────────────────────────────────


def test_results_served_from_memory(client):
    resp = client.get("/api/results")
    assert resp.status_code == 200
    body = resp.json()
    assert body  # parses and is non-empty
    # Served from the in-memory cache, byte-identical to the artifact.
    assert resp.content == main._load_precomputed()


def test_results_missing_artifact_returns_503(client, monkeypatch, tmp_path):
    monkeypatch.setattr(main, "PRECOMPUTED_FILE", tmp_path / "nope.json")
    monkeypatch.setattr(main, "_precomputed_bytes", None)
    monkeypatch.setattr(main, "_precomputed_mtime", None)
    resp = client.get("/api/results")
    assert resp.status_code == 503
    assert "precomputed.json" in resp.json()["error"]


# ── /api/rank (live) ───────────────────────────────────────────────


def test_rank_live_happy_path(client):
    resp = client.post(
        "/api/rank", files={"file": ("sample.jsonl", _demo_bytes(5), "application/jsonl")}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "live"
    assert body["metadata"]["total_candidates"] == 5
    assert 0 < len(body["candidates"]) <= 5
    first = body["candidates"][0]
    assert first["rank"] == 1
    assert "candidate_id" in first


def test_rank_live_rejects_candidate_count_over_cap(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_LIVE_CANDIDATES", 2)
    resp = client.post(
        "/api/rank", files={"file": ("sample.jsonl", _demo_bytes(3), "application/jsonl")}
    )
    assert resp.status_code == 413
    assert "capped at 2 candidates" in resp.json()["detail"]


def test_rank_live_sanitizes_uploaded_filename(client, monkeypatch):
    captured = {}

    def fake_run_ranking(in_path, out_path, config):
        captured["name"] = in_path.name
        captured["parent"] = in_path.parent
        candidate = {
            "candidate_id": "CAND_0000001",
            "profile": {
                "current_title": "Machine Learning Engineer",
                "current_company": "CRED",
                "location": "Pune",
                "country": "India",
                "years_of_experience": 7.0,
            },
            "skills": [],
            "career_history": [],
            "redrob_signals": {},
        }
        features = CandidateFeatures(
            candidate_id="CAND_0000001",
            values={name: 0.0 for name in FEATURE_NAMES},
            behavioral_multiplier=1.0,
            honeypot_multiplier=1.0,
            disqualifier_multiplier=1.0,
            flags=[],
        )
        return RankingResult(
            rows=[
                {
                    "candidate_id": "CAND_0000001",
                    "rank": 1,
                    "score": "1.000000",
                    "reasoning": "safe",
                }
            ],
            loaded_count=1,
            ranked_pool_count=1,
            bm25_backend="bm25s",
            honeypots_detected=0,
            honeypots_in_output=0,
            raw_ranked=[(candidate, features, 1.0)],
        )

    monkeypatch.setattr(main, "run_ranking", fake_run_ranking)
    resp = client.post(
        "/api/rank",
        files={"file": ("../escape.jsonl", _demo_bytes(1), "application/jsonl")},
    )
    assert resp.status_code == 200
    assert captured["name"] == "escape.jsonl"
    assert captured["parent"].name


def test_rank_live_malformed_jsonl_returns_422(client):
    resp = client.post(
        "/api/rank", files={"file": ("bad.jsonl", b"this is not json\n", "application/jsonl")}
    )
    assert resp.status_code == 422


def test_rank_live_oversize_returns_413(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_LIVE_UPLOAD_BYTES", 64)
    resp = client.post(
        "/api/rank", files={"file": ("big.jsonl", b"x" * 100, "application/jsonl")}
    )
    assert resp.status_code == 413


def test_rank_live_internal_error_does_not_leak(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("secret internal state: /etc/passwd")

    monkeypatch.setattr(main, "run_ranking", boom)
    resp = client.post(
        "/api/rank", files={"file": ("sample.jsonl", _demo_bytes(5), "application/jsonl")}
    )
    assert resp.status_code == 500
    assert "secret" not in resp.text
    assert resp.json()["error"] == "Internal ranking error."


# ── /api/batch + stream + results ──────────────────────────────────


def test_batch_full_cycle(client):
    resp = client.post(
        "/api/batch", files={"file": ("sample.jsonl", _demo_bytes(10), "application/jsonl")}
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    assert resp.json()["total_candidates"] == 10

    # TestClient runs BackgroundTasks before returning, so the job is done.
    results = client.get(f"/api/batch/{job_id}/results")
    assert results.status_code == 200
    body = results.json()
    assert body["mode"] == "batch"
    assert body["metadata"]["ranked_count"] > 0
    assert body["candidates"][0]["rank"] == 1


def test_batch_results_unknown_job_404(client):
    resp = client.get("/api/batch/batch-doesnotexist/results")
    assert resp.status_code == 404


def test_stream_unknown_job_404(client):
    resp = client.get("/api/stream/batch-doesnotexist")
    assert resp.status_code == 404


def test_batch_too_many_active_jobs_429(client):
    main.job_store.update(
        {
            "a": {"status": "processing", "started_at": "2026-01-01T00:00:00"},
            "b": {"status": "queued", "started_at": "2026-01-01T00:00:01"},
        }
    )
    resp = client.post(
        "/api/batch", files={"file": ("sample.jsonl", _demo_bytes(3), "application/jsonl")}
    )
    assert resp.status_code == 429


def test_batch_oversize_cleans_up_job_dir(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_BATCH_UPLOAD_BYTES", 64)
    before_dirs = set(p.name for p in main.JOB_DIR.iterdir())
    resp = client.post(
        "/api/batch", files={"file": ("big.jsonl", b"x" * 100, "application/jsonl")}
    )
    assert resp.status_code == 413
    after_dirs = set(p.name for p in main.JOB_DIR.iterdir())
    assert before_dirs == after_dirs  # rejected upload leaves nothing behind


def test_batch_non_utf8_returns_422(client):
    resp = client.post(
        "/api/batch", files={"file": ("bin.jsonl", b"\xff\xfe\x00\x01" * 10, "application/octet-stream")}
    )
    assert resp.status_code == 422


def test_batch_internal_error_is_sanitized(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("secret internal state: /etc/passwd")

    monkeypatch.setattr(main, "run_ranking", boom)
    resp = client.post(
        "/api/batch", files={"file": ("sample.jsonl", _demo_bytes(3), "application/jsonl")}
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    assert main.job_store[job_id]["status"] == "failed"
    assert main.job_store[job_id]["error"] == "Batch ranking failed."
    assert "secret" not in str(main.job_store[job_id])
