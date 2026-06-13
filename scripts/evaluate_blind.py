#!/usr/bin/env python3
"""ConFit v2: Evaluate Blind
Evaluates a scorer's top candidates against the frozen blind labels.
"""

import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def dcg_at_k(r, k):
    r = np.asarray(r, dtype=float)[:k]
    if r.size:
        return np.sum((2**r - 1) / np.log2(np.arange(2, r.size + 2)))
    return 0.

def ndcg_at_k(r, k, ground_truth):
    dcg_max = dcg_at_k(sorted(ground_truth, reverse=True), k)
    if not dcg_max:
        return 0.
    return dcg_at_k(r, k) / dcg_max

def main():
    frozen_path = ROOT / "blind_labels_frozen.jsonl"
    if not frozen_path.exists():
        print(f"Error: {frozen_path} missing.")
        sys.exit(1)
        
    labels = {}
    with open(frozen_path, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            labels[d["candidate_id"]] = d["consensus_label"]
            
    submission_path = ROOT / "submission.csv"
    if not submission_path.exists():
        print(f"Error: {submission_path} missing. Run rank.py first.")
        sys.exit(1)
        
    preds = []
    # parse submission.csv
    # format: candidate_id,rank,score,reasoning
    with open(submission_path, "r", encoding="utf-8") as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split(",")
            cid = parts[0]
            # only evaluate those in the blind pack
            if cid in labels:
                try:
                    score = float(parts[2])
                    preds.append((cid, score, labels[cid]))
                except ValueError:
                    pass
                    
    if not preds:
        print("No candidates from the blind pack found in submission.csv!")
        # To make it fair, we evaluate against ALL blind pack candidates
        # If they aren't in submission.csv, their predicted score is 0.0
    
    # Let's read all predictions from rank.py output or assume 0 for missing
    # Actually, we need to rank the candidates in the blind pack using the ranker!
    print("Evaluating submission.csv is limited to top 100.")
    print("For true NDCG, we must score the blind pack specifically.")
    
    sys.path.insert(0, str(ROOT / "src"))
    from redrob_ranker.features import compute_features
    from redrob_ranker.io import iter_candidates
    
    print("Scoring blind pack candidates using features.py...")
    cands_path = ROOT / "candidates.jsonl"
    blind_cands = []
    for c in iter_candidates(cands_path):
        if c["candidate_id"] in labels:
            blind_cands.append(c)
            
    r_list = []
    ground_truth = []
    pred_scores = []
    
    for c in blind_cands:
        feats = compute_features(c)
        score = feats.values.get("skill_depth_score", 0.0) * feats.behavioral_multiplier
        # Add MMoE/HyRE simulation here
        if "hyre_similarity" in feats.values:
            score += feats.values["hyre_similarity"] * 0.1
            
        true_score = labels[c["candidate_id"]]
        r_list.append((score, true_score))
        ground_truth.append(true_score)
        pred_scores.append(score)
        
    r_list.sort(key=lambda x: x[0], reverse=True)
    r = [x[1] for x in r_list]
    
    ndcg10 = ndcg_at_k(r, 10, ground_truth)
    pearson = np.corrcoef(pred_scores, ground_truth)[0, 1]
    
    print(f"\n=== FROZEN BLIND TEST EVALUATION ===")
    print(f"NDCG@10: {ndcg10:.4f}")
    print(f"Pearson: {pearson:.4f}")
    print(f"Samples: {len(r)}")
    
    if ndcg10 >= 0.85 and pearson >= 0.70:
        print("SUCCESS: Target metrics achieved.")
    else:
        print("WARNING: Target metrics not met.")

if __name__ == "__main__":
    main()
