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
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import uuid

# Add src to python path so we can import redrob_ranker
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
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


# CORS is restricted to localhost by default; set REDROB_CORS_ORIGINS on public hosts.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response

# Setup Paths
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
JOB_DIR = DATA_DIR / "jobs"

STATIC_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
JOB_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── In-memory job store for batch processing ──
# NOTE: stores are per-process. Run uvicorn with workers=1 (the default); more
# workers would split jobs/SSE streams across processes and break both.
# For multi-worker production, replace these dictionaries with Redis or another
# shared job store.
job_store: Dict[str, Dict[str, Any]] = {}
results_store: Dict[str, List[Dict]] = {}


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
        return sum(1 for line in data.splitlines() if line.strip())
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse upload: {exc}") from exc


def prune_job_stores() -> None:
    if len(job_store) <= MAX_STORED_JOBS:
        return
    oldest = sorted(job_store.items(), key=lambda item: item[1].get("started_at", ""))
    for job_id, _ in oldest[: max(0, len(job_store) - MAX_STORED_JOBS)]:
        job = job_store.pop(job_id, None)
        results_store.pop(job_id, None)
        job_path = Path(job.get("file_path", "")).parent if job else JOB_DIR / job_id
        try:
            resolved_job_path = job_path.resolve()
            resolved_root = JOB_DIR.resolve()
            if resolved_job_path != resolved_root and resolved_root in resolved_job_path.parents:
                shutil.rmtree(resolved_job_path, ignore_errors=True)
        except (OSError, RuntimeError):
            pass


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
async def rank_live(file: UploadFile = File(...)):
    """Live Proof Mode: Process ≤500 candidates synchronously, return in <2 seconds."""
    try:
        start = time.perf_counter()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            safe_name = _safe_upload_name(file.filename)
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

            result = run_ranking(
                in_path,
                out_path,
                RankerConfig(
                    top_k=100,
                    candidate_pool_size=MAX_LIVE_CANDIDATES,
                    max_candidates=MAX_LIVE_CANDIDATES,
                ),
            )

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
        # Malformed JSONL / failed submission validation — caller's input.
        raise HTTPException(status_code=422, detail=f"Could not rank upload: {e}") from e
    except Exception:
        # Never leak internals; details go to the server log only.
        _LOG.exception("live ranking failed")
        return JSONResponse({"error": "Internal ranking error.", "mode": "live"}, status_code=500)


@app.post("/api/batch")
async def batch_rank(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Batch Mode: Async processing for large files with SSE progress tracking."""
    prune_job_stores()
    active_jobs = sum(1 for j in job_store.values() if j.get("status") in ("queued", "processing"))
    if active_jobs >= 2:
        raise HTTPException(
            status_code=429,
            detail="Too many active batch jobs. Please try again later.",
        )
    job_id = f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    job_dir = JOB_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or "candidates.jsonl").name
    in_path = job_dir / safe_name
    try:
        in_path.write_bytes(await read_upload_limited(file, MAX_BATCH_UPLOAD_BYTES))

        total_lines = 0
        with open(in_path, "r", encoding="utf-8") as f:
            for _ in f:
                total_lines += 1
                if total_lines > MAX_BATCH_CANDIDATES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Batch demo is capped at {MAX_BATCH_CANDIDATES} candidates.",
                    )
    except UnicodeDecodeError as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=422, detail="Upload is not UTF-8 JSONL.") from e
    except HTTPException:
        # Rejected upload: do not leave the partial job directory behind.
        shutil.rmtree(job_dir, ignore_errors=True)
        raise

    job_store[job_id] = {
        "status": "queued",
        "processed": 0,
        "total": total_lines,
        "current_stage": "Load",
        "started_at": datetime.now().isoformat(),
        "file_path": str(in_path),
        "output_path": str(job_dir / "ranked_candidates.csv"),
        "processing_time_ms": 0,
        "honeypots": 0,
    }
    results_store[job_id] = []

    if background_tasks:
        background_tasks.add_task(process_batch_job, job_id)

    return JSONResponse({
        "job_id": job_id,
        "status": "queued",
        "total_candidates": total_lines,
        "estimated_seconds": max(total_lines * 0.0015, 1),
    })


def process_batch_job(job_id: str):
    """Background worker that updates job_store as it processes."""
    job = job_store[job_id]
    job["status"] = "processing"
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
            results_store[job_id].append(payload)
            job["processed"] = i + 1
            job["current_stage"] = "Reasoning"

        job["honeypots"] = result.honeypots_detected
        job["honeypots_in_output"] = result.honeypots_in_output
        job["ranked_pool_count"] = result.ranked_pool_count
        job["bm25_backend"] = result.bm25_backend
        job["processing_time_ms"] = round((time.perf_counter() - start) * 1000)
        job["status"] = "complete"
        job["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        _LOG.exception("batch ranking failed for job %s", job_id)
        job["status"] = "failed"
        job["error"] = "Batch ranking failed."


@app.get("/api/stream/{job_id}")
async def stream_progress(job_id: str):
    """SSE endpoint for batch job progress streaming."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        while True:
            job = job_store.get(job_id)
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
    job = job_store.get(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)

    if job["status"] != "complete":
        return JSONResponse({
            "status": job["status"],
            "processed": job["processed"],
            "total": job["total"],
            "percent": round(job["processed"] / max(job["total"], 1) * 100, 1),
        })

    candidates = results_store.get(job_id, [])

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


@app.get("/api/health")
def health_check():
    """Health check: artifact load status + build identity, never raises."""
    precomputed = _load_precomputed()
    return {
        "status": "ok",
        "version": "3.0.0",
        "git_sha": GIT_SHA,
        "modes": ["showpiece", "live", "batch"],
        "artifacts": {
            "precomputed_loaded": precomputed is not None,
            "precomputed_bytes": len(precomputed) if precomputed is not None else 0,
            "dashboard_present": (STATIC_DIR / "index.html").exists()
            or (BASE_DIR.parent.parent / "index.html").exists(),
        },
        "jobs": {
            "stored": len(job_store),
            "active": sum(1 for j in job_store.values() if j.get("status") in ("queued", "processing")),
        },
        "limits": {
            "live_candidates": MAX_LIVE_CANDIDATES,
            "batch_candidates": MAX_BATCH_CANDIDATES,
            "live_upload_mb": round(MAX_LIVE_UPLOAD_BYTES / (1024 * 1024), 2),
            "batch_upload_mb": round(MAX_BATCH_UPLOAD_BYTES / (1024 * 1024), 2),
        },
    }
