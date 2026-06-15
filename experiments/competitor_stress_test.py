"""Stress-test the competitors' blind-proxy 'lead' under stricter evaluation.

The top cluster (us + the 3 ranked above) sits within +0.0033 composite on the 100K
blind set. Three tests for whether that lead is a GENUINE technique advantage or
proxy-overfit noise:

  1. SELECTION OVERLAP - if the top submissions pick ~the same 100 candidates, score
     gaps are pure ordering, not better candidate discovery.
  2. CROSS-LABEL CONSISTENCY - re-rank the submissions on 7 independent judge label
     sets. A genuine lead stays on top; an overfit lead shuffles.
  3. REPEATED-HOLDOUT SIGNIFICANCE - bootstrap the blind labels; is C_i > us stable,
     or does the sign flip across resamples (i.e., inside the noise band)?
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import hashlib  # noqa: E402

import numpy as np  # noqa: E402

from redrob_ranker.eval_harness import LabelSet, evaluate, load_labels  # noqa: E402

CX = Path("C:/Users/bhune/_cx/competitor_top100.json")
LAB = Path("C:/Users/bhune/india-runs-compare-lab/artifacts")
SETS = ["h2_availblind_labels", "merged_j1", "merged_j2", "merged_j3",
        "relabel_j4", "relabel_g25", "blind_test_frozen"]


def read_ids(p):
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig", newline="")))
    km = {(k or "").strip().lower(): k for k in rows[0].keys()}
    cid, rk = km.get("candidate_id"), km.get("rank")
    if rk:
        rows.sort(key=lambda r: int(float(r.get(rk) or 1e9)))
    return [(r.get(cid) or "").strip() for r in rows][:100]


def main():
    R = {}
    for i, (repo, ids) in enumerate(json.load(open(CX)).items(), 1):
        R[f"C{i}"] = ids
    R["US"] = read_ids(Path("submission.csv"))
    fr = Path("experiments/fusion_raw_submission.csv")
    if fr.exists():
        R["fusion-raw"] = read_ids(fr)

    # 1. selection overlap with US
    us = set(R["US"])
    print("== selection overlap with our golden top-100 (Jaccard / shared count) ==")
    for k, ids in R.items():
        if k == "US":
            continue
        s = set(ids); j = len(s & us) / len(s | us)
        print(f"  {k:<12} shared={len(s & us):>3}/100  jaccard={j:.2f}")

    # 2. cross-label consistency: composite per submission per label set + rank
    print("\n== cross-label composite (and rank among submissions) ==")
    labelsets = {}
    for name in SETS:
        p = LAB / f"{name}.jsonl"
        if p.exists():
            labelsets[name] = load_labels(p)
    hdr = f"{'set':<20}" + "".join(f"{k:>11}" for k in R)
    print(hdr)
    rank_of_us = []
    for name, ls in labelsets.items():
        comps = {k: evaluate(ids, ls).composite for k, ids in R.items()}
        order = sorted(comps, key=lambda k: -comps[k])
        us_rank = order.index("US") + 1
        rank_of_us.append((name, us_rank))
        row = "".join(f"{comps[k]:>11.4f}" for k in R)
        print(f"{name:<20}{row}")
    print("\nour rank among submissions, per label set:")
    for name, r in rank_of_us:
        print(f"  {name:<20} US ranks #{r} of {len(R)}")

    # 3. repeated-holdout significance vs US on the blind set
    full = labelsets["h2_availblind_labels"]
    print("\n== repeated-holdout (R=50) on blind set: P(C_i > US) ==")
    splits = []
    for s in range(50):
        te = {c: v for c, v in full.tiers.items()
              if int(hashlib.md5((c + "|" + str(s)).encode()).hexdigest(), 16) % 2}
        splits.append(LabelSet("te", te, {c: full.gains[c] for c in te}))
    us_ids = R["US"]
    for k, ids in R.items():
        if k == "US":
            continue
        d = np.array([evaluate(ids, te).composite - evaluate(us_ids, te).composite for te in splits])
        print(f"  {k:<12} mean {d.mean():+.4f}  std {d.std():.4f}  P(>US) {int((d>0).sum())}/50  "
              f"min {d.min():+.4f} max {d.max():+.4f}")


if __name__ == "__main__":
    main()
