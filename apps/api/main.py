"""FastAPI hybrid-mode real-time dashboard with glassmorphic UI backend."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import asyncio
import time
import shutil
import gzip
import io
import threading
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import uuid
import secrets
import sqlite3  # noqa: F401 — kept for sqlite3.OperationalError in health checks

# Add src to python path so we can import redrob_ranker
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from redrob_ranker.payload import build_candidate_payload
from redrob_ranker.pipeline import RankerConfig, run_ranking

_LOG = logging.getLogger("redrob.api")

app = FastAPI(
    title="Redrob HireFit Ranker",
    version="3.0.0",
    description="Hybrid-mode real-time candidate ranking dashboard. Showpiece + Live Proof + Batch."
)

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


MAX_LIVE_CANDIDATES = _env_int("REDROB_MAX_LIVE_CANDIDATES", 500)
MAX_BATCH_CANDIDATES = _env_int("REDROB_MAX_BATCH_CANDIDATES", 5000)
MAX_LIVE_UPLOAD_BYTES = _env_int("REDROB_MAX_LIVE_UPLOAD_BYTES", 2 * 1024 * 1024)
MAX_BATCH_UPLOAD_BYTES = _env_int("REDROB_MAX_BATCH_UPLOAD_BYTES", 16 * 1024 * 1024)
MAX_STORED_JOBS = _env_int("REDROB_MAX_STORED_JOBS", 20)
MAX_ACTIVE_BATCH_JOBS = _env_int("REDROB_MAX_ACTIVE_BATCH_JOBS", 2)
RATE_LIMIT_PER_MINUTE = _env_int("REDROB_RATE_LIMIT_PER_MINUTE", 120)
RATE_LIMIT_WINDOW_SECONDS = _env_int("REDROB_RATE_LIMIT_WINDOW_SECONDS", 60)
# Local dev plus the deployed dashboard (same-origin in production; listed so
# preview hosts and the Render origin work without env overrides).
_DEFAULT_ORIGINS = (
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,"
    "https://redrob-hirefit-ranker.onrender.com"
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("REDROB_CORS_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
STARTED_AT = time.time()
# Optional demo auth gate. Set REDROB_DEMO_TOKEN env in production to require
# an X-Demo-Token header on write endpoints. Unset = open for local dev.
DEMO_TOKEN = os.getenv("REDROB_DEMO_TOKEN", "").strip()
ALLOWED_UPLOAD_SUFFIXES = {
    (".jsonl",),
    (".json",),
    (".gz",),
    (".jsonl", ".gz"),
}


_metrics_lock = threading.Lock()
_rate_lock = threading.Lock()
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_metrics: dict[str, Any] = {
    "requests_total": 0,
    "request_seconds_sum": 0.0,
    "responses_by_status": defaultdict(int),
    "requests_by_route": defaultdict(int),
    "rate_limited_total": 0,
    "live_rank_total": 0,
    "live_rank_failures_total": 0,
    "batch_jobs_total": 0,
    "batch_jobs_completed_total": 0,
    "batch_jobs_failed_total": 0,
}


# CORS is restricted to localhost by default; set REDROB_CORS_ORIGINS on public hosts.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _route_key(path: str) -> str:
    if path.startswith("/api/stream/"):
        return "/api/stream/{job_id}"
    if path.startswith("/api/batch/"):
        tail = path.removeprefix("/api/batch/").split("/")
        if len(tail) >= 2 and tail[1] == "results":
            return "/api/batch/{job_id}/results"
        if len(tail) >= 2 and tail[1] == "download":
            return "/api/batch/{job_id}/download"
        return "/api/batch/{job_id}"
    return path


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def _check_rate_limit(request: Request) -> int | None:
    if RATE_LIMIT_PER_MINUTE <= 0 or request.method != "POST":
        return None
    if request.url.path not in {"/api/rank", "/api/batch"}:
        return None

    now = time.monotonic()
    cutoff = now - max(RATE_LIMIT_WINDOW_SECONDS, 1)
    key = f"{_client_key(request)}:{request.url.path}"
    with _rate_lock:
        bucket = _rate_buckets[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_MINUTE:
            retry_after = max(1, int(bucket[0] + RATE_LIMIT_WINDOW_SECONDS - now))
            _inc_metric("rate_limited_total")
            return retry_after
        bucket.append(now)
    return None


def _record_request(method: str, path: str, status_code: int, seconds: float) -> None:
    route = _route_key(path)
    with _metrics_lock:
        _metrics["requests_total"] += 1
        _metrics["request_seconds_sum"] += seconds
        _metrics["responses_by_status"][str(status_code)] += 1
        _metrics["requests_by_route"][f"{method} {route}"] += 1


def _inc_metric(name: str, value: int = 1) -> None:
    with _metrics_lock:
        _metrics[name] += value


@app.middleware("http")
async def add_operational_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id", "").strip() or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    retry_after = _check_rate_limit(request)
    if retry_after is not None:
        response = JSONResponse(
            {"error": "Rate limit exceeded.", "retry_after_seconds": retry_after},
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )
    else:
        try:
            response = await call_next(request)
        except Exception:
            _record_request(request.method, request.url.path, 500, time.perf_counter() - start)
            _LOG.exception("request failed request_id=%s path=%s", request_id, request.url.path)
            raise

    seconds = time.perf_counter() - start
    _record_request(request.method, request.url.path, response.status_code, seconds)
    response.headers.setdefault("X-Request-ID", request_id)
    response.headers.setdefault("Server-Timing", f"app;dur={seconds * 1000:.1f}")
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    _LOG.info(
        "request method=%s path=%s status=%s duration_ms=%.1f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        seconds * 1000,
        request_id,
    )
    return response

# Setup Paths
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
JOB_DIR = DATA_DIR / "jobs"

STATIC_DIR.mkdir(exist_ok=True)

# Setup Paths
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
JOB_DIR = DATA_DIR / "jobs"

STATIC_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
JOB_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── Persistent SQLite job store (apps/api/data/jobs.db) ─────────────────
# JobStore is thread-safe (internal RLock + WAL SQLite). Jobs survive process
# restarts and are inspectable with: sqlite3 apps/api/data/jobs.db
# Run uvicorn with workers=1; SSE streams are per-process and cannot be shared
# across workers without an external pub/sub layer.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from _job_store import JobStore  # noqa: E402

_store = JobStore(DATA_DIR / "jobs.db")


def _resolve_git_sha() -> str:
    """Best-effort short SHA: env override first, then .git/HEAD (no git binary)."""
    env_sha = os.getenv("REDROB_GIT_SHA", "").strip()
    if env_sha:
        return env_sha[:12]
    try:
        git_dir = BASE_DIR.parent.parent / ".git"
        if git_dir.is_file():
            pointer = git_dir.read_text(encoding="utf-8").strip()
            if pointer.startswith("gitdir:"):
                git_dir = (BASE_DIR.parent.parent / pointer.split(":", 1)[1].strip()).resolve()

        def read_git_file(rel: str) -> str:
            path = git_dir / rel
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
            common_file = git_dir / "commondir"
            if common_file.exists():
                common_dir = (git_dir / common_file.read_text(encoding="utf-8").strip()).resolve()
                common_path = common_dir / rel
                if common_path.exists():
                    return common_path.read_text(encoding="utf-8").strip()
            raise OSError(f"git file not found: {rel}")

        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref:"):
            ref = head.split(None, 1)[1]
            return read_git_file(ref)[:12]
        return head[:12]
    except OSError:
        return "unknown"


GIT_SHA = _resolve_git_sha()
PRECOMPUTED_FILE = DATA_DIR / "precomputed.json"

# Showpiece payload, loaded once and served from memory (O(1), no per-request
# disk read). _load_precomputed() can be retried lazily if the file appears
# after startup.
_precomputed_bytes: bytes | None = None
_precomputed_mtime: float | None = None


def _load_precomputed() -> bytes | None:
    """(Re)load precomputed.json into memory if present and changed on disk."""
    global _precomputed_bytes, _precomputed_mtime
    try:
        mtime = PRECOMPUTED_FILE.stat().st_mtime
    except OSError:
        _precomputed_bytes = None
        _precomputed_mtime = None
        return None
    if _precomputed_bytes is None or mtime != _precomputed_mtime:
        try:
            raw = PRECOMPUTED_FILE.read_bytes()
            json.loads(raw)  # refuse to cache a corrupt artifact
        except (OSError, ValueError):
            _precomputed_bytes = None
            _precomputed_mtime = None
            return None
        _precomputed_bytes = raw
        _precomputed_mtime = mtime
    return _precomputed_bytes


_load_precomputed()


async def read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds {max_bytes // (1024 * 1024)} MB demo limit.",
        )
    return data


def _safe_upload_name(filename: str | None) -> str:
    safe_name = Path(filename or "candidates.jsonl").name
    return safe_name or "candidates.jsonl"


def _validate_upload_name(filename: str | None) -> str:
    safe_name = _safe_upload_name(filename)
    suffixes = tuple(s.lower() for s in Path(safe_name).suffixes)
    if suffixes not in ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail="Upload must be .jsonl, .json, .jsonl.gz, or .gz.",
        )
    return safe_name


def _uploaded_candidate_count(data: bytes, filename: str) -> int:
    """Count uploaded records before ranking so demo caps are explicit."""
    suffixes = [s.lower() for s in Path(filename).suffixes]
    try:
        if suffixes[-2:] == [".jsonl", ".gz"] or suffixes[-1:] == [".gz"]:
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
                return sum(1 for line in f if line.strip())
        if suffixes[-1:] == [".json"]:
            parsed = json.loads(data.decode("utf-8-sig"))
            if not isinstance(parsed, list):
                raise ValueError("JSON upload must be an array of candidates.")
            return len(parsed)
        text = data.decode("utf-8-sig")
        return sum(1 for line in text.splitlines() if line.strip())
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse upload: {exc}") from exc


def _active_job_count() -> int:
    return _store.count_active()


def _check_demo_token(request: Request) -> None:
    """Raise 401 if REDROB_DEMO_TOKEN is set and the header is missing/wrong."""
    if not DEMO_TOKEN:
        return
    header = request.headers.get("X-Demo-Token", "").strip()
    if not secrets.compare_digest(header, DEMO_TOKEN):
        raise HTTPException(
            status_code=401,
            detail="X-Demo-Token header required. Contact the demo owner for access.",
        )


def _dashboard_present() -> bool:
    return (STATIC_DIR / "index.html").exists() or (BASE_DIR.parent.parent / "index.html").exists()


def _job_snapshot(job_id: str) -> dict | None:
    job = _store.get_job(job_id)
    if not job:
        return None
    safe = {
        "job_id": job_id,
        "status": job.get("status"),
        "processed": job.get("processed", 0),
        "total": job.get("total", 0),
        "percent": round(job.get("processed", 0) / max(job.get("total", 0), 1) * 100, 1),
        "current_stage": job.get("current_stage"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "processing_time_ms": job.get("processing_time_ms", 0),
        "honeypots": job.get("honeypots", 0),
        "honeypots_in_output": job.get("honeypots_in_output", 0),
        "ranked_pool_count": job.get("ranked_pool_count", 0),
        "bm25_backend": job.get("bm25_backend") or "unknown",
    }
    if job.get("status") == "failed":
        safe["error"] = job.get("error", "Batch ranking failed.")
    if job.get("status") == "complete":
        safe["results_url"] = f"/api/batch/{job_id}/results"
        safe["download_url"] = f"/api/batch/{job_id}/download"
    return safe


def prune_job_stores() -> None:
    _store.prune(MAX_STORED_JOBS, JOB_DIR)


def extract_candidate_payload(
    candidate: dict,
    features: Any,
    score: float,
    rank: int,
    reasoning: str,
    *,
    max_score: float | None = None,
) -> dict:
    """Build a rich UI payload from actual feature/multiplier objects."""
    return build_candidate_payload(
        candidate,
        features,
        score,
        rank,
        reasoning,
        max_score=max_score,
    )


# ═══════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════

@app.get("/")
def index():
    """Serve the single-file HTML dashboard."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        root_index = BASE_DIR.parent.parent / "index.html"
        if root_index.exists():
            return FileResponse(root_index)
        return JSONResponse(
            {"error": "index.html not found in static folder or repository root. Run the setup script."},
            status_code=503,
        )
    return FileResponse(index_file)


@app.get("/api/results")
def get_results():
    """Showpiece Mode: serve the pre-computed 100K payload from memory."""
    payload = _load_precomputed()
    if payload is None:
        return JSONResponse(
            {
                "error": "precomputed.json not found. Run: python scripts/generate_precomputed.py",
                "hint": "This file is generated from your 100K run and enables the instant-load showpiece mode.",
            },
            status_code=503,
        )
    return Response(content=payload, media_type="application/json")


@app.post("/api/rank")
async def rank_live(request: Request, file: UploadFile = File(...)):
    """Live Proof Mode: Process ≤500 candidates synchronously, return in <2 seconds."""
    _check_demo_token(request)
    try:
        start = time.perf_counter()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            safe_name = _validate_upload_name(file.filename)
            in_path = base / safe_name
            out_path = base / "ranked_candidates.csv"

            upload_bytes = await read_upload_limited(file, MAX_LIVE_UPLOAD_BYTES)
            uploaded_count = _uploaded_candidate_count(upload_bytes, safe_name)
            if uploaded_count > MAX_LIVE_CANDIDATES:
                raise HTTPException(
                    status_code=413,
                    detail=f"Live demo is capped at {MAX_LIVE_CANDIDATES} candidates.",
                )
            in_path.write_bytes(upload_bytes)

            result = await asyncio.to_thread(
                run_ranking,
                in_path,
                out_path,
                RankerConfig(
                    top_k=100,
                    candidate_pool_size=MAX_LIVE_CANDIDATES,
                    max_candidates=MAX_LIVE_CANDIDATES,
                ),
            )
            _inc_metric("live_rank_total")

            candidates_json = []
            raw = result.raw_ranked or []
            selected_raw = raw[: len(result.rows)]
            max_score = selected_raw[0][2] if selected_raw else 0.0
            for i, (candidate, features, score) in enumerate(selected_raw):
                reasoning = result.rows[i]["reasoning"] if i < len(result.rows) else ""
                payload = extract_candidate_payload(
                    candidate,
                    features,
                    score,
                    i + 1,
                    reasoning,
                    max_score=max_score,
                )
                candidates_json.append(payload)

            # Pipeline stages metadata
            pipeline_stages = [
                {"name": "Load", "status": "complete", "count": result.loaded_count},
                {"name": "Text", "status": "complete", "count": result.loaded_count},
                {"name": "BM25", "status": "complete", "count": result.ranked_pool_count},
                {"name": "28-D Features", "status": "complete", "count": result.ranked_pool_count},
                {"name": "Honeypot", "status": "complete", "count": result.honeypots_detected},
                {"name": "Behavioral", "status": "complete", "count": result.ranked_pool_count},
                {"name": "Rank", "status": "complete", "count": len(candidates_json)},
                {"name": "Reasoning", "status": "complete", "count": len(candidates_json)},
            ]

            return JSONResponse({
                "mode": "live",
                "metadata": {
                    "total_candidates": result.loaded_count,
                    "ranked_count": len(candidates_json),
                    "honeypots_blocked": result.honeypots_detected,
                    "avg_score": round(sum(c["score"] for c in candidates_json) / max(len(candidates_json), 1), 4),
                    "processing_time_ms": round((time.perf_counter() - start) * 1000),
                    "bm25_backend": result.bm25_backend,
                    "honeypots_in_output": result.honeypots_in_output,
                },
                "pipeline": pipeline_stages,
                "candidates": candidates_json,
            })
    except HTTPException:
        raise
    except ValueError as e:
        _inc_metric("live_rank_failures_total")
        # Malformed JSONL / failed submission validation — caller's input.
        raise HTTPException(status_code=422, detail=f"Could not rank upload: {e}") from e
    except Exception:
        _inc_metric("live_rank_failures_total")
        # Never leak internals; details go to the server log only.
        _LOG.exception("live ranking failed")
        return JSONResponse({"error": "Internal ranking error.", "mode": "live"}, status_code=500)


@app.post("/api/batch")
async def batch_rank(request: Request, file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Batch Mode: Async processing for large files with SSE progress tracking."""
    _check_demo_token(request)
    prune_job_stores()
    active_jobs = _active_job_count()
    if active_jobs >= MAX_ACTIVE_BATCH_JOBS:
        raise HTTPException(
            status_code=429,
            detail="Too many active batch jobs. Please try again later.",
        )
    job_id = f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    job_dir = JOB_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _validate_upload_name(file.filename)
    in_path = job_dir / safe_name
    try:
        upload_bytes = await read_upload_limited(file, MAX_BATCH_UPLOAD_BYTES)
        total_lines = _uploaded_candidate_count(upload_bytes, safe_name)
        if total_lines > MAX_BATCH_CANDIDATES:
            raise HTTPException(
                status_code=413,
                detail=f"Batch demo is capped at {MAX_BATCH_CANDIDATES} candidates.",
            )
        in_path.write_bytes(upload_bytes)
    except HTTPException:
        # Rejected upload: do not leave the partial job directory behind.
        shutil.rmtree(job_dir, ignore_errors=True)
        raise

    _store.create_job(
        job_id=job_id,
        total=total_lines,
        file_path=str(in_path),
        output_path=str(job_dir / "ranked_candidates.csv"),
        started_at=datetime.now().isoformat(),
    )
    _inc_metric("batch_jobs_total")

    if background_tasks:
        background_tasks.add_task(process_batch_job, job_id)

    return JSONResponse({
        "job_id": job_id,
        "status": "queued",
        "total_candidates": total_lines,
        "estimated_seconds": max(total_lines * 0.0015, 1),
    })


def process_batch_job(job_id: str):
    """Background worker that writes progress to the persistent SQLite job store."""
    job = _store.get_job(job_id)
    if not job:
        _LOG.error("process_batch_job: job_id=%s not found in store", job_id)
        return
    _store.update_job(job_id, status="processing")
    _store.log_event(job_id, "started")
    start = time.perf_counter()

    try:
        in_path = Path(job["file_path"])
        out_path = Path(job["output_path"])

        result = run_ranking(
            in_path,
            out_path,
            RankerConfig(
                top_k=100,
                candidate_pool_size=MAX_BATCH_CANDIDATES,
                max_candidates=MAX_BATCH_CANDIDATES,
            ),
        )

        raw = result.raw_ranked or []
        selected_raw = raw[: len(result.rows)]
        max_score = selected_raw[0][2] if selected_raw else 0.0
        payloads: list[dict] = []
        for i, (candidate, features, score) in enumerate(selected_raw):
            reasoning = result.rows[i]["reasoning"] if i < len(result.rows) else ""
            payload = extract_candidate_payload(
                candidate,
                features,
                score,
                i + 1,
                reasoning,
                max_score=max_score,
            )
            payloads.append(payload)
            # Throttled DB progress updates: write every 50 candidates to
            # reduce contention while keeping SSE latency acceptable.
            if (i + 1) % 50 == 0 or i == len(selected_raw) - 1:
                _store.update_job(job_id, processed=i + 1, current_stage="Reasoning")

        _store.add_results(job_id, payloads)
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        _store.update_job(
            job_id,
            honeypots=result.honeypots_detected,
            honeypots_in_output=result.honeypots_in_output,
            ranked_pool_count=result.ranked_pool_count,
            bm25_backend=result.bm25_backend,
            processing_time_ms=elapsed_ms,
            status="complete",
            completed_at=datetime.now().isoformat(),
        )
        _store.log_event(job_id, "completed", f"elapsed_ms={elapsed_ms}")
        _inc_metric("batch_jobs_completed_total")

    except Exception:
        _LOG.exception("batch ranking failed for job %s", job_id)
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        _store.update_job(
            job_id,
            status="failed",
            error="Batch ranking failed.",
            processing_time_ms=elapsed_ms,
        )
        _store.log_event(job_id, "failed")
        _inc_metric("batch_jobs_failed_total")


@app.get("/api/stream/{job_id}")
async def stream_progress(job_id: str):
    """SSE endpoint for batch job progress streaming."""
    if _job_snapshot(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        while True:
            job = _store.get_job(job_id) or {}
            if not job:
                # Job pruned mid-stream.
                yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                break

            percent = round(job["processed"] / max(job["total"], 1) * 100, 1)

            # Single-line f-string expression: multi-line f-string expressions
            # are PEP 701 (Python 3.12+) and a SyntaxError on 3.11.
            progress_event = json.dumps({
                "type": "progress",
                "processed": job["processed"],
                "total": job["total"],
                "percent": percent,
                "stage": job["current_stage"],
                "status": job["status"],
            })
            yield f"data: {progress_event}\n\n"

            if job["status"] in ("complete", "failed"):
                if job["status"] == "complete":
                    yield f"data: {json.dumps({'type': 'complete', 'results_url': f'/api/batch/{job_id}/results'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': job.get('error', 'Unknown error')})}\n\n"
                break

            await asyncio.sleep(0.5)  # Throttle to 2 updates/sec

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/batch/{job_id}/results")
def get_batch_results(job_id: str):
    """Get completed batch job results."""
    snapshot = _job_snapshot(job_id)
    if not snapshot:
        return JSONResponse({"error": "Job not found"}, status_code=404)

    job = _store.get_job(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    candidates = _store.get_results(job_id) if job.get("status") == "complete" else []

    if job["status"] != "complete":
        return JSONResponse({
            "status": job["status"],
            "processed": job["processed"],
            "total": job["total"],
            "percent": round(job["processed"] / max(job["total"], 1) * 100, 1),
        })

    pipeline_stages = [
        {"name": "Load", "status": "complete", "count": job["total"]},
        {"name": "Text", "status": "complete", "count": job["total"]},
        {"name": "BM25", "status": "complete", "count": job.get("ranked_pool_count", job["total"])},
        {"name": "28-D Features", "status": "complete", "count": job.get("ranked_pool_count", job["total"])},
        {"name": "Honeypot", "status": "complete", "count": job.get("honeypots", 0)},
        {"name": "Behavioral", "status": "complete", "count": job.get("ranked_pool_count", job["total"])},
        {"name": "Rank", "status": "complete", "count": len(candidates)},
        {"name": "Reasoning", "status": "complete", "count": len(candidates)},
    ]

    return JSONResponse({
        "mode": "batch",
        "metadata": {
            "total_candidates": job["total"],
            "ranked_count": len(candidates),
            "honeypots_blocked": job.get("honeypots", 0),
            "avg_score": round(sum(c["score"] for c in candidates) / max(len(candidates), 1), 4),
            "processing_time_ms": job.get("processing_time_ms", 0),
            "bm25_backend": job.get("bm25_backend", "unknown"),
            "honeypots_in_output": job.get("honeypots_in_output", 0),
        },
        "pipeline": pipeline_stages,
        "candidates": candidates,
    })


@app.get("/api/batch/{job_id}")
def get_batch_status(job_id: str):
    """Return sanitized batch job state without exposing filesystem paths."""
    snapshot = _job_snapshot(job_id)
    if not snapshot:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return snapshot


@app.get("/api/batch/{job_id}/download")
def download_batch_csv(job_id: str):
    """Download the completed CSV artifact for a batch job."""
    snapshot = _job_snapshot(job_id)
    if not snapshot:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    if snapshot["status"] != "complete":
        return JSONResponse({"error": "Batch job is not complete.", "status": snapshot["status"]}, status_code=409)
    job_full = _store.get_job(job_id)
    out_path = Path(job_full["output_path"]) if job_full else None
    if not out_path or not out_path.exists():
        return JSONResponse({"error": "Batch CSV artifact is missing."}, status_code=410)
    return FileResponse(
        out_path,
        media_type="text/csv",
        filename=f"{job_id}-ranked_candidates.csv",
    )


@app.get("/api/health")
def health_check():
    """Health check: artifact load status + build identity, never raises."""
    precomputed = _load_precomputed()
    return {
        "status": "ok",
        "version": "3.0.0",
        "git_sha": GIT_SHA,
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
        "modes": ["showpiece", "live", "batch"],
        "artifacts": {
            "precomputed_loaded": precomputed is not None,
            "precomputed_bytes": len(precomputed) if precomputed is not None else 0,
            "dashboard_present": _dashboard_present(),
        },
        "jobs": {
            "stored": _store.count_stored(),
            "active": _store.count_active(),
            "max_active": MAX_ACTIVE_BATCH_JOBS,
        },
        "limits": {
            "live_candidates": MAX_LIVE_CANDIDATES,
            "batch_candidates": MAX_BATCH_CANDIDATES,
            "live_upload_mb": round(MAX_LIVE_UPLOAD_BYTES / (1024 * 1024), 2),
            "batch_upload_mb": round(MAX_BATCH_UPLOAD_BYTES / (1024 * 1024), 2),
            "rate_limit_per_minute": RATE_LIMIT_PER_MINUTE,
        },
    }


@app.get("/api/healthz")
def healthz():
    """Kubernetes/Render-style liveness alias."""
    return health_check()


@app.get("/api/readyz")
def readiness_check():
    """Readiness check: fail closed if the dashboard artifact is not deploy-ready."""
    precomputed = _load_precomputed()
    ready = precomputed is not None and _dashboard_present()
    body = {
        "status": "ready" if ready else "degraded",
        "version": "3.0.0",
        "git_sha": GIT_SHA,
        "checks": {
            "precomputed_loaded": precomputed is not None,
            "dashboard_present": _dashboard_present(),
            "job_store_available": _store.is_writable(),
        },
    }
    return JSONResponse(body, status_code=200 if ready else 503)


def _metric_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


@app.get("/api/metrics")
def metrics():
    """Prometheus-style plain-text metrics for demo ops visibility."""
    precomputed = _load_precomputed()
    with _metrics_lock:
        snapshot = {
            "requests_total": _metrics["requests_total"],
            "request_seconds_sum": _metrics["request_seconds_sum"],
            "responses_by_status": dict(_metrics["responses_by_status"]),
            "requests_by_route": dict(_metrics["requests_by_route"]),
            "rate_limited_total": _metrics["rate_limited_total"],
            "live_rank_total": _metrics["live_rank_total"],
            "live_rank_failures_total": _metrics["live_rank_failures_total"],
            "batch_jobs_total": _metrics["batch_jobs_total"],
            "batch_jobs_completed_total": _metrics["batch_jobs_completed_total"],
            "batch_jobs_failed_total": _metrics["batch_jobs_failed_total"],
        }

    lines = [
        "# HELP redrob_api_requests_total Total HTTP requests.",
        "# TYPE redrob_api_requests_total counter",
        f"redrob_api_requests_total {snapshot['requests_total']}",
        "# HELP redrob_api_request_seconds_sum Cumulative request latency.",
        "# TYPE redrob_api_request_seconds_sum counter",
        f"redrob_api_request_seconds_sum {snapshot['request_seconds_sum']:.6f}",
        "# HELP redrob_api_uptime_seconds Process uptime.",
        "# TYPE redrob_api_uptime_seconds gauge",
        f"redrob_api_uptime_seconds {time.time() - STARTED_AT:.3f}",
        "# HELP redrob_api_precomputed_loaded Whether the showpiece artifact is loaded.",
        "# TYPE redrob_api_precomputed_loaded gauge",
        f"redrob_api_precomputed_loaded {1 if precomputed is not None else 0}",
        "# HELP redrob_api_jobs_stored In-memory batch jobs currently retained.",
        "# TYPE redrob_api_jobs_stored gauge",
        f"redrob_api_jobs_stored {_store.count_stored()}",
        "# HELP redrob_api_jobs_active Active queued/processing batch jobs.",
        "# TYPE redrob_api_jobs_active gauge",
        f"redrob_api_jobs_active {_active_job_count()}",
        "# HELP redrob_api_rate_limited_total Requests rejected by in-process rate limit.",
        "# TYPE redrob_api_rate_limited_total counter",
        f"redrob_api_rate_limited_total {snapshot['rate_limited_total']}",
        "# HELP redrob_api_live_rank_total Successful live rank requests.",
        "# TYPE redrob_api_live_rank_total counter",
        f"redrob_api_live_rank_total {snapshot['live_rank_total']}",
        "# HELP redrob_api_live_rank_failures_total Failed live rank requests.",
        "# TYPE redrob_api_live_rank_failures_total counter",
        f"redrob_api_live_rank_failures_total {snapshot['live_rank_failures_total']}",
        "# HELP redrob_api_batch_jobs_total Accepted batch jobs.",
        "# TYPE redrob_api_batch_jobs_total counter",
        f"redrob_api_batch_jobs_total {snapshot['batch_jobs_total']}",
        f"redrob_api_batch_jobs_completed_total {snapshot['batch_jobs_completed_total']}",
        f"redrob_api_batch_jobs_failed_total {snapshot['batch_jobs_failed_total']}",
    ]
    for status, count in sorted(snapshot["responses_by_status"].items()):
        lines.append(f'redrob_api_responses_total{{status="{_metric_label(status)}"}} {count}')
    for route, count in sorted(snapshot["requests_by_route"].items()):
        method, _, path = route.partition(" ")
        lines.append(
            'redrob_api_route_requests_total{'
            f'method="{_metric_label(method)}",path="{_metric_label(path)}"'
            f"}} {count}"
        )
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
