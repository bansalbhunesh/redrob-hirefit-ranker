#!/usr/bin/env python3
"""ConFit v2 RUM: Hard Negative Validation
Verifies that the depth scoring and heuristic stack naturally catches
>95% of the mined hard negatives.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.features import compute_features

def main():
    negatives_path = ROOT / "rum_hard_negatives.jsonl"
    if not negatives_path.exists():
        print(f"Error: {negatives_path} not found. Run rum_mine.py first.")
        sys.exit(1)
        
    candidates = []
    with open(negatives_path, "r", encoding="utf-8") as f:
        for line in f:
            candidates.append(json.loads(line))
            
    print(f"Loaded {len(candidates)} hard negatives.")
    
    caught_count = 0
    total = len(candidates)
    
    for c in candidates:
        feats = compute_features(c)
        
        # A candidate is "caught" if the baseline heuristics severely penalize them
        # (e.g., honeypot < 1.0, disqualifier > 0, keyword_stuffer > 0)
        # OR if their final role depth score is low.
        
        caught = False
        if feats.honeypot_multiplier < 0.5:
            caught = True
        elif feats.values.get("disqualifier_skill_flag", 0) > 0.5:
            caught = True
        elif feats.values.get("keyword_stuffer_flag", 0) > 0.5:
            caught = True
        elif feats.values.get("skill_depth_score", 1.0) < 0.2:
            caught = True
            
        if caught:
            caught_count += 1
            
    if total == 0:
        print("No candidates found.")
        sys.exit(1)
        
    catch_rate = caught_count / total
    print(f"Caught {caught_count}/{total} hard negatives ({catch_rate:.2%})")
    
    if catch_rate >= 0.95:
        print("SUCCESS: Depth scoring catches >95% of mined negatives.")
    else:
        print("WARNING: Catch rate is <95%. Tune depth thresholds.")

if __name__ == "__main__":
    main()
