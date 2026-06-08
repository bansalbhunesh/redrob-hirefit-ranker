"""FastAPI hybrid-mode real-time dashboard."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Add src to python path so we can import redrob_ranker
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from redrob_ranker.pipeline import RankerConfig, run_ranking

app = FastAPI(title="Redrob Candidate Ranker", version="2.0.0")

# Setup Paths
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

STATIC_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def index():
    """Serve the single-file HTML dashboard."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse({"error": "index.html not found in static folder."})
    return FileResponse(index_file)

@app.get("/api/results")
def get_results():
    """Showpiece Mode: Serve the pre-computed 100K results instantly."""
    precomputed_file = DATA_DIR / "precomputed.json"
    if not precomputed_file.exists():
        return JSONResponse({"error": "precomputed.json not found. Run generate_data first."})
    return FileResponse(precomputed_file)

@app.post("/api/rank")
async def rank_live(file: UploadFile = File(...)):
    """Live Proof Mode: Process small JSONL files synchronously and return JSON."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        in_path = base / (file.filename or "candidates.jsonl")
        out_path = base / "ranked_candidates.csv"
        
        in_path.write_bytes(await file.read())
        
        # We limit max_candidates to 500 for the Live Proof mode to keep it <2 seconds
        result = run_ranking(
            in_path,
            out_path,
            RankerConfig(top_k=100, candidate_pool_size=500, max_candidates=500),
        )
        
        # `result.raw_ranked` has (candidate, features, score). We can construct the UI payload.
        results_json = []
        for i, (candidate, features, score) in enumerate(result.raw_ranked or []):
            cid = candidate.get("candidate_id", "Unknown")
            prof = candidate.get("profile", {})
            reasoning = result.rows[i]["reasoning"] if i < len(result.rows) else ""
            
            results_json.append({
                "candidate_id": cid,
                "rank": i + 1,
                "score": score,
                "reasoning": reasoning,
                "title": prof.get("current_title", "Unknown"),
                "company": prof.get("current_company", "Unknown"),
                "yoe": float(prof.get("years_of_experience", 0.0)),
                "location": prof.get("location", "Unknown")
            })
            
    return JSONResponse({
        "metadata": {
            "total_candidates": result.loaded_count,
            "ranked_count": result.ranked_pool_count,
            "honeypots_blocked": result.honeypots_detected,
        },
        "candidates": results_json
    })
