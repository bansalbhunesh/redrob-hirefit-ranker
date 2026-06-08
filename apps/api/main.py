"""FastAPI hybrid-mode real-time dashboard with glassmorphic UI backend."""

from __future__ import annotations

import json
import sys
import tempfile
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Add src to python path so we can import redrob_ranker
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from redrob_ranker.payload import build_candidate_payload
from redrob_ranker.pipeline import RankerConfig, run_ranking

app = FastAPI(
    title="Redrob HireFit Ranker",
    version="3.0.0",
    description="Hybrid-mode real-time candidate ranking dashboard. Showpiece + Live Proof + Batch."
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
job_store: Dict[str, Dict[str, Any]] = {}
results_store: Dict[str, List[Dict]] = {}


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
        return JSONResponse({"error": "index.html not found in static folder. Run the setup script."})
    return FileResponse(index_file)


@app.get("/api/results")
def get_results():
    """Showpiece Mode: Serve pre-computed 100K results instantly."""
    precomputed_file = DATA_DIR / "precomputed.json"
    if not precomputed_file.exists():
        return JSONResponse({
            "error": "precomputed.json not found. Run: python scripts/generate_precomputed.py",
            "hint": "This file is generated from your 100K run and enables the instant-load showpiece mode."
        })
    return FileResponse(precomputed_file)


@app.post("/api/rank")
async def rank_live(file: UploadFile = File(...)):
    """Live Proof Mode: Process ≤500 candidates synchronously, return in <2 seconds."""
    try:
        start = time.perf_counter()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            in_path = base / (file.filename or "candidates.jsonl")
            out_path = base / "ranked_candidates.csv"

            in_path.write_bytes(await file.read())

            result = run_ranking(
                in_path,
                out_path,
                RankerConfig(top_k=100, candidate_pool_size=500, max_candidates=500),
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
    except Exception as e:
        return JSONResponse({"error": str(e), "mode": "live"}, status_code=500)


@app.post("/api/batch")
async def batch_rank(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Batch Mode: Async processing for large files with SSE progress tracking."""
    job_id = f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    job_dir = JOB_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or "candidates.jsonl").name
    in_path = job_dir / safe_name
    in_path.write_bytes(await file.read())

    total_lines = 0
    with open(in_path, "r", encoding="utf-8") as f:
        for _ in f:
            total_lines += 1

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
            RankerConfig(top_k=100, candidate_pool_size=100000, max_candidates=100000),
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
        job["status"] = "failed"
        job["error"] = str(e)


@app.get("/api/stream/{job_id}")
async def stream_progress(job_id: str):
    """SSE endpoint for batch job progress streaming."""
    async def event_generator():
        while True:
            job = job_store.get(job_id)
            if not job:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                break

            percent = round(job["processed"] / max(job["total"], 1) * 100, 1)

            yield f"data: {json.dumps({
                'type': 'progress',
                'processed': job['processed'],
                'total': job['total'],
                'percent': percent,
                'stage': job['current_stage'],
                'status': job['status']
            })}\n\n"

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
    """Health check endpoint."""
    return {"status": "ok", "version": "3.0.0", "modes": ["showpiece", "live", "batch"]}
