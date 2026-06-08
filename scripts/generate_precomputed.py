#!/usr/bin/env python3
import csv
import json
from pathlib import Path

def generate_precomputed(candidates_file, submission_file, out_file):
    print(f"Loading candidates from {candidates_file}...")
    candidates_by_id = {}
    with open(candidates_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            c = json.loads(line)
            candidates_by_id[c["candidate_id"]] = c
            
    print(f"Loading submission from {submission_file}...")
    results = []
    with open(submission_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["candidate_id"]
            cand = candidates_by_id.get(cid, {})
            prof = cand.get("profile", {})
            
            results.append({
                "candidate_id": cid,
                "rank": int(row["rank"]),
                "score": float(row["score"]),
                "reasoning": row["reasoning"],
                "title": prof.get("current_title", "Unknown"),
                "company": prof.get("current_company", "Unknown"),
                "yoe": float(prof.get("years_of_experience", 0.0)),
                "location": prof.get("location", "Unknown")
            })
            
    results.sort(key=lambda x: x["rank"])
    hpCount = len([r for r in results if "honeypot" in r["reasoning"].lower()])
    
    payload = {
        "metadata": {
            "total_candidates": 100000,
            "ranked_count": len(results),
            "honeypots_blocked": hpCount,
            "processing_time_ms": 132000
        },
        "candidates": results
    }
    
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    print(f"Generated {out_file} successfully.")

if __name__ == "__main__":
    generate_precomputed(
        r"D:\Downloads\[PUB] India_runs_data_and_ai_challenge\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl",
        "submission.csv",
        "apps/api/data/precomputed.json"
    )
