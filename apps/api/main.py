"""FastAPI demo wrapper for small candidate samples."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response

from redrob_ranker.pipeline import RankerConfig, run_ranking

app = FastAPI(title="Redrob Candidate Ranker", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/rank")
async def rank(file: UploadFile = File(...)) -> Response:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        in_path = base / (file.filename or "candidates.json")
        out_path = base / "ranked_candidates.csv"
        in_path.write_bytes(await file.read())
        run_ranking(
            in_path,
            out_path,
            RankerConfig(top_k=100, candidate_pool_size=200, max_candidates=100),
        )
        content = out_path.read_bytes()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ranked_candidates.csv"'},
    )
