"""FastAPI hybrid-mode real-time dashboard with glassmorphic UI backend."""

from __future__ import annotations

import json
import sys
import tempfile
import asyncio
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

STATIC_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── In-memory job store for batch processing ──
job_store: Dict[str, Dict[str, Any]] = {}
results_store: Dict[str, List[Dict]] = {}


def extract_candidate_payload(candidate: dict, features: dict, score: float, rank: int, reasoning: str) -> dict:
    """Build a rich UI payload from pipeline output."""
    prof = candidate.get("profile", {})
    redrob = candidate.get("redrob_signals", {})
    skills = candidate.get("skills", [])
    education = candidate.get("education", [])
    career = candidate.get("career_history", [])
    certs = candidate.get("certifications", [])
    langs = candidate.get("languages", [])

    # Honeypot detection from reasoning
    honeypot_flag = "honeypot" in reasoning.lower()
    honeypot_reasons = []
    if honeypot_flag:
        # Extract specific honeypot reasons from reasoning
        hp_keywords = [
            "impossible timeline", "expert-zero-duration", "multiple current jobs",
            "salary inversion", "education impossibility", "endorsement inflation",
            "title-description contradiction", "skill-duration paradox"
        ]
        for kw in hp_keywords:
            if kw.lower() in reasoning.lower():
                honeypot_reasons.append(kw.replace("-", " ").title())
        if not honeypot_reasons:
            honeypot_reasons.append("Honeypot Detected")

    # Build feature breakdown (generic, handles any feature dict)
    feature_breakdown = {}
    if features and isinstance(features, dict):
        for key, val in features.items():
            if isinstance(val, (int, float)):
                feature_breakdown[key] = round(float(val), 4)

    # Behavioral signals
    behavioral = {
        "profile_completeness": redrob.get("profile_completeness_score", 0),
        "open_to_work": redrob.get("open_to_work_flag", False),
        "response_rate": redrob.get("recruiter_response_rate", 0),
        "avg_response_time": redrob.get("avg_response_time_hours", 0),
        "interview_completion": redrob.get("interview_completion_rate", 0),
        "offer_acceptance": redrob.get("offer_acceptance_rate", 0),
        "github_activity": redrob.get("github_activity_score", 0),
        "saved_by_recruiters": redrob.get("saved_by_recruiters_30d", 0),
        "profile_views": redrob.get("profile_views_received_30d", 0),
        "notice_period": redrob.get("notice_period_days", 0),
        "verified_email": redrob.get("verified_email", False),
        "verified_phone": redrob.get("verified_phone", False),
        "skill_assessments": redrob.get("skill_assessment_scores", {}),
        "connection_count": redrob.get("connection_count", 0),
        "endorsements": redrob.get("endorsements_received", 0),
        "expected_salary": redrob.get("expected_salary_range_inr_lpa", {}),
        "preferred_work_mode": redrob.get("preferred_work_mode", "unknown"),
        "willing_to_relocate": redrob.get("willing_to_relocate", False),
    }

    # Career timeline
    timeline = []
    for job in career:
        timeline.append({
            "company": job.get("company", "Unknown"),
            "title": job.get("title", "Unknown"),
            "start": job.get("start_date", ""),
            "end": job.get("end_date", "Present"),
            "duration_months": job.get("duration_months", 0),
            "is_current": job.get("is_current", False),
            "industry": job.get("industry", "Unknown"),
            "company_size": job.get("company_size", "Unknown"),
        })

    # Skills cloud
    skills_cloud = []
    for sk in skills:
        skills_cloud.append({
            "name": sk.get("name", "Unknown"),
            "proficiency": sk.get("proficiency", "unknown"),
            "endorsements": sk.get("endorsements", 0),
            "duration_months": sk.get("duration_months", 0),
        })

    # Education
    edu_list = []
    for ed in education:
        edu_list.append({
            "institution": ed.get("institution", "Unknown"),
            "degree": ed.get("degree", "Unknown"),
            "field": ed.get("field_of_study", "Unknown"),
            "start": ed.get("start_year", ""),
            "end": ed.get("end_year", ""),
            "grade": ed.get("grade", ""),
            "tier": ed.get("tier", "unknown"),
        })

    # Certifications
    cert_list = [c.get("name", "Unknown") for c in certs]

    # Languages
    lang_list = [{"language": l.get("language", ""), "proficiency": l.get("proficiency", "")} for l in langs]

    # Determine tier
    tier = "standard"
    if rank == 1:
        tier = "gold"
    elif rank == 2:
        tier = "silver"
    elif rank == 3:
        tier = "bronze"
    elif honeypot_flag:
        tier = "honeypot"

    return {
        "candidate_id": candidate.get("candidate_id", "Unknown"),
        "rank": rank,
        "score": round(score, 4),
        "tier": tier,
        "honeypot_flag": honeypot_flag,
        "honeypot_reasons": honeypot_reasons,
        "reasoning": reasoning,
        "features": feature_breakdown,
        "behavioral": behavioral,
        "profile": {
            "name": prof.get("anonymized_name", "Unknown"),
            "headline": prof.get("headline", ""),
            "summary": prof.get("summary", ""),
            "title": prof.get("current_title", "Unknown"),
            "company": prof.get("current_company", "Unknown"),
            "company_size": prof.get("current_company_size", "Unknown"),
            "industry": prof.get("current_industry", "Unknown"),
            "location": prof.get("location", "Unknown"),
            "country": prof.get("country", "Unknown"),
            "yoe": float(prof.get("years_of_experience", 0.0)),
        },
        "timeline": timeline,
        "skills": skills_cloud,
        "education": edu_list,
        "certifications": cert_list,
        "languages": lang_list,
    }


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
            for i, (candidate, features, score) in enumerate(raw):
                reasoning = result.rows[i]["reasoning"] if i < len(result.rows) else ""
                payload = extract_candidate_payload(candidate, features, score, i + 1, reasoning)
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
                    "processing_time_ms": 0,  # Could be measured
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

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        in_path = base / (file.filename or "candidates.jsonl")
        in_path.write_bytes(await file.read())

        # Count total lines for progress
        total_lines = 0
        with open(in_path, "r", encoding="utf-8") as f:
            for _ in f:
                total_lines += 1

        # Store job state
        job_store[job_id] = {
            "status": "queued",
            "processed": 0,
            "total": total_lines,
            "current_stage": "Load",
            "started_at": datetime.now().isoformat(),
            "file_path": str(in_path),
            "output_path": str(base / "ranked_candidates.csv"),
        }
        results_store[job_id] = []

        # Start background processing
        if background_tasks:
            background_tasks.add_task(process_batch_job, job_id)

        return JSONResponse({
            "job_id": job_id,
            "status": "queued",
            "total_candidates": total_lines,
            "estimated_seconds": max(total_lines * 0.0015, 1),  # ~1.5ms per candidate
        })


def process_batch_job(job_id: str):
    """Background worker that updates job_store as it processes."""
    job = job_store[job_id]
    job["status"] = "processing"

    try:
        in_path = Path(job["file_path"])
        out_path = Path(job["output_path"])

        result = run_ranking(
            in_path,
            out_path,
            RankerConfig(top_k=100, candidate_pool_size=100000, max_candidates=100000),
        )

        raw = result.raw_ranked or []
        for i, (candidate, features, score) in enumerate(raw):
            reasoning = result.rows[i]["reasoning"] if i < len(result.rows) else ""
            payload = extract_candidate_payload(candidate, features, score, i + 1, reasoning)
            results_store[job_id].append(payload)
            job["processed"] = i + 1
            job["current_stage"] = "Reasoning"

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
        {"name": "BM25", "status": "complete", "count": job["total"]},
        {"name": "28-D Features", "status": "complete", "count": job["total"]},
        {"name": "Honeypot", "status": "complete", "count": job.get("honeypots", 0)},
        {"name": "Behavioral", "status": "complete", "count": job["total"]},
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
            "processing_time_ms": 0,
        },
        "pipeline": pipeline_stages,
        "candidates": candidates,
    })


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "3.0.0", "modes": ["showpiece", "live", "batch"]}
