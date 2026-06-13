#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.eval_harness import evaluate_many, load_labels

def main():
    if len(sys.argv) > 1:
        sub_path = Path(sys.argv[1])
    else:
        sub_path = ROOT / "submission.csv"
        
    if not sub_path.exists():
        print(f"Error: {sub_path} not found.")
        sys.exit(1)
        
    df = pd.read_csv(sub_path)
    submission_ids = df["candidate_id"].tolist()
    
    label_path = ROOT / "artifacts" / "blind_test_frozen.jsonl"
    if not label_path.exists():
        print(f"Error: {label_path} not found.")
        sys.exit(1)
        
    labels = load_labels(label_path, "blind-frozen-1000")
    
    print(f"Evaluating {len(submission_ids)} candidates against frozen blind pack...")
    results, mean = evaluate_many(submission_ids, [labels], unlabeled="exclude")
    
    for r in results:
        row = r.as_row()
        print(f"  {row['label_set']:<18} NDCG@10={row['ndcg10']:.4f} "
              f"NDCG@50={row['ndcg50']:.4f} MAP={row['map']:.4f} "
              f"P@10={row['p10']:.4f} composite={row['composite']:.4f} "
              f"coverage={row['coverage']:.1%}")
              
    print(f"\nFinal Mean Composite: {mean:.4f}")

if __name__ == "__main__":
    main()
