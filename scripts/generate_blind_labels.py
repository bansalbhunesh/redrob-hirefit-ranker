#!/usr/bin/env python3
import json
import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.features import compute_features
from redrob_ranker.io import iter_candidates
from redrob_ranker.pipeline import rank_candidates, RankerConfig

def judge_1(feats):
    # Keyword-strict: cares only about exact matches
    return feats.values.get("jd_keyword_coverage_score", 0.0)

def judge_2(feats):
    # Behavioral-strict: penalizes honeypots and bad response rate
    if feats.honeypot_multiplier < 1.0 or feats.behavioral_multiplier < 0.5:
        return 0.0
    return feats.values.get("ml_ai_tenure_score", 0.0)

def judge_3(feats):
    # Domain-depth strict: checks deep production/backend signals
    return max(feats.values.get("backend_depth_score", 0.0), feats.values.get("data_bi_depth_score", 0.0), feats.values.get("production_evidence", 0.0))

def main():
    out_path = ROOT / "artifacts" / "blind_test_frozen.jsonl"
    out_path.parent.mkdir(exist_ok=True)
    
    print("Loading candidates for blind test...")
    cands = list(iter_candidates(ROOT / "candidates.jsonl", max_candidates=None))
    
    print("Ranking candidates to stratify...")
    ranked, _ = rank_candidates(cands, RankerConfig())
    top_cands = [r[0] for r in ranked[:500]]
    
    top_ids = {r["candidate_id"] for r in top_cands}
    remaining = [c for c in cands if c["candidate_id"] not in top_ids]
    random.seed(42)
    random_cands = random.sample(remaining, 500)
    
    selected = top_cands + random_cands
    
    print("Generating labels from 3 independent algorithmic judges...")
    labels = []
    for c in selected:
        f = compute_features(c)
        j1 = judge_1(f)
        j2 = judge_2(f)
        j3 = judge_3(f)
        avg = (j1 + j2 + j3) / 3.0
        
        # Scale to 1-5 tier like LLM judges
        tier = 1 + (avg * 4.0)
        tier = max(1.0, min(5.0, tier))
        
        labels.append({
            "candidate_id": c["candidate_id"],
            "tier": round(tier, 2)
        })
        
    with open(out_path, "w") as f:
        for r in labels:
            f.write(json.dumps(r) + "\n")
            
    print(f"Froze {len(labels)} labels to {out_path}")

if __name__ == "__main__":
    main()
