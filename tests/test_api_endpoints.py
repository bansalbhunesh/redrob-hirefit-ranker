"""Endpoint tests for the FastAPI dashboard backend (apps/api/main.py).

Covers, for each route: happy path, not-found, and malformed input. Uses the
bundled demo_sample.jsonl so live/batch ranking runs the real pipeline on a
small pool (serial path, no process pool).
"""

from __future__ import annotations

import json
import gzip
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
MANIFEST = json.loads((ROOT / "docs" / "metrics_manifest.json").read_text(encoding="utf-8"))


@pytest.fixture()
def client(tmp_path):
    from apps.api._job_store import JobStore

    # Give each test a fresh isolated DB so tests don't bleed state.
    test_store = JobStore(tmp_path / "test_jobs.db")
    main._store = test_store
    with main._rate_lock:
        main._rate_buckets.clear()
    with main._metrics_lock:
        main._metrics["requests_total"] = 0
        main._metrics["request_seconds_sum"] = 0.0
        main._metrics["responses_by_status"].clear()
        main._metrics["requests_by_route"].clear()
        main._metrics["rate_limited_total"] = 0
        main._metrics["live_rank_total"] = 0
        main._metrics["live_rank_failures_total"] = 0
        main._metrics["batch_jobs_total"] = 0
        main._metrics["batch_jobs_completed_total"] = 0
        main._metrics["batch_jobs_failed_total"] = 0
    with TestClient(main.app) as c:
        yield c


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


def _git_head_resolvable() -> bool:
    """True only if .git/HEAD (following worktree gitdir pointers) is actually
    readable in THIS environment. Mirrors apps.api.main._resolve_git_sha so the
    assertion below never fails merely because a worktree `.git` pointer cannot be
    resolved here (e.g. a git worktree mounted into a container without its parent
    gitdir, or a slim image with no git binary) — in those cases "unknown" is the
    correct, graceful result and must not fail the suite."""
    try:
        git_dir = ROOT / ".git"
        if not git_dir.exists():
            return False
        if git_dir.is_file():
            pointer = git_dir.read_text(encoding="utf-8").strip()
            if pointer.startswith("gitdir:"):
                git_dir = (ROOT / pointer.split(":", 1)[1].strip()).resolve()
        return (git_dir / "HEAD").exists()
    except OSError:
        return False


def test_health_reports_artifacts_and_sha(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == MANIFEST["submission"]["api_version"]
    assert body["git_sha"] and body["git_sha"] != ""
    if _git_head_resolvable():
        assert body["git_sha"] != "unknown"
    assert body["artifacts"]["precomputed_loaded"] is True
    assert body["artifacts"]["precomputed_bytes"] > 0
    assert body["artifacts"]["dashboard_present"] is True
    assert {"stored", "active"} <= set(body["jobs"])
    assert body["jobs"]["max_active"] == main.MAX_ACTIVE_BATCH_JOBS
    assert body["limits"]["rate_limit_per_minute"] == main.RATE_LIMIT_PER_MINUTE
    assert body["limits"]["expanded_upload_mb"] == 32.0
    assert body["limits"]["candidate_record_mb"] == 1.0
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["x-request-id"]
    assert "app;dur=" in resp.headers["server-timing"]
    # /api/healthz is the k8s/Render liveness alias — same payload, must also be live (folded
    # here to keep the suite count stable; closes the one uncovered route in Phase 3).
    alias = client.get("/api/healthz")
    assert alias.status_code == 200
    assert alias.json()["status"] == "ok"


def test_readyz_reports_ready(client):
    resp = client.get("/api/readyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["precomputed_loaded"] is True
    assert body["checks"]["dashboard_present"] is True


def test_readyz_degraded_when_showpiece_artifact_missing(client, monkeypatch, tmp_path):
    monkeypatch.setattr(main, "PRECOMPUTED_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(main, "_precomputed_bytes", None)
    monkeypatch.setattr(main, "_precomputed_mtime", None)
    resp = client.get("/api/readyz")
    assert resp.status_code == 503
    assert resp.json()["status"] == "degraded"


def test_metrics_endpoint_reports_requests_and_jobs(client):
    client.get("/api/health")
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    text = resp.text
    assert "redrob_api_requests_total" in text
    assert 'redrob_api_route_requests_total{method="GET",path="/api/health"}' in text
    assert "redrob_api_jobs_active" in text


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
    assert "33 Features" in {stage["name"] for stage in body["pipeline"]}
    assert not any("28" in stage["name"] for stage in body["pipeline"])
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


def test_rank_live_rejects_unsupported_upload_extension(client):
    resp = client.post(
        "/api/rank", files={"file": ("sample.txt", _demo_bytes(1), "text/plain")}
    )
    assert resp.status_code == 415
    assert ".jsonl" in resp.json()["detail"]


def test_post_rate_limit_is_enforced_before_ranking(client, monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT_PER_MINUTE", 1)
    monkeypatch.setattr(main, "RATE_LIMIT_WINDOW_SECONDS", 60)
    first = client.post(
        "/api/rank",
        headers={"x-forwarded-for": "203.0.113.10"},
        files={"file": ("bad.jsonl", b"not json\n", "application/jsonl")},
    )
    assert first.status_code == 422
    second = client.post(
        "/api/rank",
        # A caller-controlled XFF value must not create a fresh rate-limit key.
        headers={"x-forwarded-for": "198.51.100.44"},
        files={"file": ("bad.jsonl", b"not json\n", "application/jsonl")},
    )
    assert second.status_code == 429
    assert second.headers["retry-after"]
    assert second.json()["error"] == "Rate limit exceeded."


def test_rank_live_rejects_gzip_expansion_over_safety_limit(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_EXPANDED_UPLOAD_BYTES", 64)
    expanded = b'{"candidate_id":"CAND_0000001","profile":{}}\n' * 4
    payload = gzip.compress(expanded)
    resp = client.post(
        "/api/rank",
        files={"file": ("sample.jsonl.gz", payload, "application/gzip")},
    )
    assert resp.status_code == 413
    assert "Expanded gzip" in resp.json()["detail"]


def test_rank_live_rejects_oversized_plain_jsonl_record(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_CANDIDATE_RECORD_BYTES", 32)
    resp = client.post(
        "/api/rank",
        files={
            "file": (
                "sample.jsonl",
                b'{"candidate_id":"CAND_0000001","profile":{}}\n',
                "application/jsonl",
            )
        },
    )
    assert resp.status_code == 413
    assert "candidate record" in resp.json()["detail"]


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
    assert "33 Features" in {stage["name"] for stage in body["pipeline"]}
    assert body["candidates"][0]["rank"] == 1

    status = client.get(f"/api/batch/{job_id}")
    assert status.status_code == 200
    status_body = status.json()
    assert status_body["status"] == "complete"
    assert status_body["results_url"] == f"/api/batch/{job_id}/results"
    assert status_body["download_url"] == f"/api/batch/{job_id}/download"
    assert "file_path" not in status_body
    assert "output_path" not in status_body

    download = client.get(f"/api/batch/{job_id}/download")
    assert download.status_code == 200
    assert "text/csv" in download.headers["content-type"]
    assert b"candidate_id,rank,score,reasoning" in download.content[:100]


def test_batch_results_unknown_job_404(client):
    resp = client.get("/api/batch/batch-doesnotexist/results")
    assert resp.status_code == 404


def test_batch_status_unknown_job_404(client):
    resp = client.get("/api/batch/batch-doesnotexist")
    assert resp.status_code == 404


def test_batch_download_pending_job_returns_409(client, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "JOB_DIR", tmp_path)
    job_dir = tmp_path / "batch-pending"
    job_dir.mkdir()
    in_path = job_dir / "sample.jsonl"
    in_path.write_text("{}", encoding="utf-8")
    out_path = job_dir / "ranked_candidates.csv"
    main._store.create_job(
        job_id="batch-pending",
        total=1,
        file_path=str(in_path),
        output_path=str(out_path),
        started_at="2026-06-12T00:00:00",
    )
    resp = client.get("/api/batch/batch-pending/download")
    assert resp.status_code == 409
    assert resp.json()["status"] == "queued"


def test_stream_unknown_job_404(client):
    resp = client.get("/api/stream/batch-doesnotexist")
    assert resp.status_code == 404


def test_batch_too_many_active_jobs_429(client):
    main._store.create_job(job_id="a", total=1, file_path="/tmp/a", output_path="/tmp/a.csv", started_at="2026-01-01T00:00:00")
    main._store.update_job("a", status="processing")
    main._store.create_job(job_id="b", total=1, file_path="/tmp/b", output_path="/tmp/b.csv", started_at="2026-01-01T00:00:01")
    main._store.update_job("b", status="queued")
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


def test_batch_rejects_unsupported_upload_extension(client):
    resp = client.post(
        "/api/batch", files={"file": ("sample.txt", _demo_bytes(1), "text/plain")}
    )
    assert resp.status_code == 415


def test_batch_internal_error_is_sanitized(client, monkeypatch):
    import time

    def boom(*args, **kwargs):
        raise RuntimeError("secret internal state: /etc/passwd")

    monkeypatch.setattr(main, "run_ranking", boom)
    resp = client.post(
        "/api/batch", files={"file": ("sample.jsonl", _demo_bytes(3), "application/jsonl")}
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    # Background thread needs a moment to process and write the failed status.
    for _ in range(20):
        job = main._store.get_job(job_id)
        if job and job["status"] == "failed":
            break
        time.sleep(0.1)
    job = main._store.get_job(job_id)
    assert job is not None
    assert job["status"] == "failed"
    assert job["error"] == "Batch ranking failed."
    assert "secret" not in json.dumps(job)
