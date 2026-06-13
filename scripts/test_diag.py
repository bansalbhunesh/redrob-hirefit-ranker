import json
import sys
import time
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.io import iter_candidates
from redrob_ranker.features import compute_features

print("Starting diagnostic...")
cands = list(iter_candidates(ROOT / "candidates.jsonl", max_candidates=5))
print(f"Loaded {len(cands)} candidates.")

for i, c in enumerate(cands):
    print(f"\nProcessing candidate {i+1}/{len(cands)}...")
    t0 = time.time()
    feats = compute_features(c)
    t1 = time.time()
    print(f"Done in {t1-t0:.4f} seconds.")
    print(f"Score: {feats.values.get('confit_similarity_score')}")

print("Diagnostic complete.")
