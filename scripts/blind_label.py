#!/usr/bin/env python3
"""ConFit v2: Blind Label Generation
Creates 500 frozen blind labels from 3 independent synthetic judges.
"""

import json
import os
import sys
import random
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.io import iter_candidates
from redrob_ranker.features import compute_features

# Simple synthetic judges simulating different evaluator personas
def judge_pessimistic(feats) -> float:
    # Strict multiplicative gates
    if feats.honeypot_multiplier < 0.5:
        return 0.0
    if feats.values.get("disqualifier_skill_flag", 0) > 0.0:
        return 0.0
    
    score = feats.values.get("skill_depth_score", 0.0) * feats.values.get("production_evidence", 0.0)
    score *= feats.behavioral_multiplier
    return score

def judge_strict_domain(feats) -> float:
    # High threshold on depth, ignores soft behavioral signals
    if feats.honeypot_multiplier < 1.0:
        return 0.0
    
    depth = max(
        feats.values.get("backend_depth_score", 0.0),
        feats.values.get("data_bi_depth_score", 0.0),
        feats.values.get("skill_depth_score", 0.0)
    )
    if depth < 0.4:
        return 0.0
        
    return (depth + feats.values.get("production_evidence", 0.0)) / 2.0

def judge_lenient_holistic(feats) -> float:
    # Averages out skills without hard zeroing unless severe
    if feats.honeypot_multiplier < 0.2:
        return 0.0
        
    base = (
        feats.values.get("skill_depth_score", 0.0) * 0.4 +
        feats.values.get("production_evidence", 0.0) * 0.3 +
        feats.values.get("yoe_fit_score", 0.0) * 0.2 +
        feats.values.get("education_score", 0.0) * 0.1
    )
    return base * feats.behavioral_multiplier

def main():
    cands_path = ROOT / "candidates.jsonl"
    print(f"Loading candidates from {cands_path}...")
    
    # We want 500 candidates representing a good mix of qualities
    candidates = []
    
    # We will sample 10,000 to find 500 diverse ones
    pool = []
    for i, c in enumerate(iter_candidates(cands_path)):
        pool.append(c)
        if len(pool) >= 10000:
            break
            
    # Compute features to stratify
    print("Computing features for pool...")
    pool_feats = []
    for c in pool:
        pool_feats.append((c, compute_features(c)))
        
    # Stratify by depth score to ensure balanced label distribution
    pool_feats.sort(key=lambda x: x[1].values.get("skill_depth_score", 0.0), reverse=True)
    
    # Take top 200, bottom 100, and middle 200
    selected = pool_feats[:200] + pool_feats[-100:] + pool_feats[len(pool_feats)//2 - 100 : len(pool_feats)//2 + 100]
    
    print(f"Selected {len(selected)} candidates for blind labeling.")
    
    labels = []
    for cand, feats in selected:
        j1 = judge_pessimistic(feats)
        j2 = judge_strict_domain(feats)
        j3 = judge_lenient_holistic(feats)
        
        scores = [j1, j2, j3]
        consensus = float(np.mean(scores))
        std_dev = float(np.std(scores))
        
        labels.append({
            "candidate_id": cand["candidate_id"],
            "judge_pessimistic": j1,
            "judge_strict": j2,
            "judge_lenient": j3,
            "consensus_label": consensus,
            "disagreement_std": std_dev
        })
        
    out_path = ROOT / "blind_labels_frozen.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for lbl in labels:
            f.write(json.dumps(lbl) + "\n")
            
    print(f"Saved {len(labels)} blind labels to {out_path}")
    
    # Freeze the file
    try:
        os.chmod(out_path, 0o444)
        print("Locked file to read-only (chmod 444).")
    except Exception as e:
        print(f"Warning: Could not chmod file: {e}")

if __name__ == "__main__":
    main()
