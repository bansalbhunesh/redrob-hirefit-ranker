#!/usr/bin/env python3
"""Generate the dashboard showpiece payload from a submission CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.features import compute_features  # noqa: E402
from redrob_ranker.payload import build_candidate_payload  # noqa: E402


def _load_candidates(path: Path) -> dict[str, dict]:
    candidates_by_id: dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            candidate = json.loads(line)
            candidates_by_id[candidate["candidate_id"]] = candidate
    return candidates_by_id


def _load_submission(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: int(row["rank"]))
    return rows


def generate_precomputed(
    candidates_file: Path,
    submission_file: Path,
    out_file: Path,
    *,
    total_candidates: int | None,
    processing_time_ms: int | None,
    bm25_backend: str | None,
    honeypots_blocked: int | None,
    honeypots_in_output: int | None,
) -> None:
    print(f"Loading candidates from {candidates_file}...")
    candidates_by_id = _load_candidates(candidates_file)

    print(f"Loading submission from {submission_file}...")
    submission_rows = _load_submission(submission_file)
    raw_scores = [float(row["score"]) for row in submission_rows]
    max_score = max(raw_scores, default=0.0)

    payload_rows = []
    for row in submission_rows:
        candidate = candidates_by_id.get(row["candidate_id"])
        if not candidate:
            raise SystemExit(f"Candidate {row['candidate_id']} from submission is missing in dataset.")
        features = compute_features(candidate)
        features.total = float(row["score"])
        payload_rows.append(
            build_candidate_payload(
                candidate,
                features,
                float(row["score"]),
                int(row["rank"]),
                row["reasoning"],
                max_score=max_score,
            )
        )

    top_honeypots = sum(1 for item in payload_rows if item["honeypot_flag"])
    metadata = {
        "total_candidates": total_candidates or len(candidates_by_id),
        "ranked_count": len(payload_rows),
        "honeypots_blocked": honeypots_blocked if honeypots_blocked is not None else top_honeypots,
        "honeypots_in_output": honeypots_in_output if honeypots_in_output is not None else top_honeypots,
        "avg_score": round(sum(row["score"] for row in payload_rows) / max(len(payload_rows), 1), 4),
    }
    if processing_time_ms is not None:
        metadata["processing_time_ms"] = processing_time_ms
    if bm25_backend:
        metadata["bm25_backend"] = bm25_backend

    payload = {
        "mode": "showpiece",
        "metadata": metadata,
        "pipeline": [
            {"name": "Load", "status": "complete", "count": metadata["total_candidates"]},
            {"name": "Text", "status": "complete", "count": metadata["total_candidates"]},
            {"name": "BM25", "status": "complete", "count": metadata["total_candidates"]},
            {"name": "28-D Features", "status": "complete", "count": metadata["total_candidates"]},
            {"name": "Honeypot", "status": "complete", "count": metadata["honeypots_blocked"]},
            {"name": "Behavioral", "status": "complete", "count": metadata["total_candidates"]},
            {"name": "Rank", "status": "complete", "count": len(payload_rows)},
            {"name": "Reasoning", "status": "complete", "count": len(payload_rows)},
        ],
        "candidates": payload_rows,
    }

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(f"Generated {out_file} with {len(payload_rows)} ranked candidates.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate API showpiece JSON from a ranked CSV.")
    parser.add_argument("--candidates", required=True, type=Path, help="Path to candidates.jsonl")
    parser.add_argument("--submission", default=Path("submission.csv"), type=Path, help="Ranked CSV")
    parser.add_argument(
        "--out",
        default=Path("apps/api/data/precomputed.json"),
        type=Path,
        help="Output JSON payload path",
    )
    parser.add_argument("--total-candidates", type=int, default=None)
    parser.add_argument("--processing-time-ms", type=int, default=None)
    parser.add_argument("--bm25-backend", default=None)
    parser.add_argument("--honeypots-blocked", type=int, default=None)
    parser.add_argument("--honeypots-in-output", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_precomputed(
        args.candidates,
        args.submission,
        args.out,
        total_candidates=args.total_candidates,
        processing_time_ms=args.processing_time_ms,
        bm25_backend=args.bm25_backend,
        honeypots_blocked=args.honeypots_blocked,
        honeypots_in_output=args.honeypots_in_output,
    )


if __name__ == "__main__":
    main()
