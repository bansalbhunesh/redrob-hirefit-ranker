#!/usr/bin/env python3
"""Score a submission CSV against an independent labels file using the challenge's
composite:  0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10.

Labels file: JSONL with {"candidate_id", "tier"} (0..5). Works with either
build_independent_labels.py (heuristic, non-circular) or llm_judge_labels.py.

P@10 uses tier>=3 ("relevant") per submission_spec.md section 4. MAP is binary
at tier>=3 with AP computed over the submitted ranking (documented approximation;
only relative deltas between ranker variants are meaningful here).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from redrob_ranker.eval import dcg, ndcg_at_k  # noqa: E402

RELEVANT_TIER = 3.0


def load_submission(path: Path) -> list[str]:
    rows = sorted(csv.DictReader(open(path, encoding="utf-8")), key=lambda r: int(r["rank"]))
    return [r["candidate_id"] for r in rows]


def load_labels(path: Path) -> tuple[dict[str, float], dict[str, float]]:
    """Return (tier_by_id, gain_by_id).

    tier  -> integer relevance (for binary P@10 / MAP, spec section 4)
    gain  -> continuous relevance if present, else tier (for graded NDCG ordering)
    """
    tiers: dict[str, float] = {}
    gains: dict[str, float] = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        cid = rec["candidate_id"]
        tier = float(rec.get("tier", rec.get("silver_label", 0)))
        tiers[cid] = tier
        gains[cid] = float(rec.get("relevance", tier))
    return tiers, gains


def precision_at_k(ranked, labels, k, thr=RELEVANT_TIER):
    if k <= 0:
        return 0.0
    return sum(1 for cid in ranked[:k] if labels.get(cid, 0.0) >= thr) / k


def average_precision(ranked, labels, thr=RELEVANT_TIER):
    total_relevant = sum(1 for v in labels.values() if v >= thr)
    if total_relevant == 0:
        return 0.0
    denom = min(total_relevant, len(ranked))
    hits = 0
    psum = 0.0
    for i, cid in enumerate(ranked, start=1):
        if labels.get(cid, 0.0) >= thr:
            hits += 1
            psum += hits / i
    return psum / denom


def main() -> None:
    ap = argparse.ArgumentParser(description="Score a submission against independent labels.")
    ap.add_argument("--submission", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--label-source", default="independent-heuristic",
                    help="Annotation for the report header (e.g. 'llm-judge').")
    args = ap.parse_args()

    ranked = load_submission(args.submission)
    tiers, gains = load_labels(args.labels)
    covered = sum(1 for cid in ranked if cid in tiers)

    ndcg10 = ndcg_at_k(ranked, gains, 10)        # graded gain -> discriminates ordering
    ndcg50 = ndcg_at_k(ranked, gains, 50)
    mapv = average_precision(ranked, tiers)      # binary tier>=3
    p10 = precision_at_k(ranked, tiers, 10)
    composite = 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * mapv + 0.05 * p10

    relevant = sum(1 for v in tiers.values() if v >= RELEVANT_TIER)
    top10_tiers = [tiers.get(cid, 0.0) for cid in ranked[:10]]
    print(f"Submission : {args.submission}")
    print(f"Labels     : {args.labels}  (source: {args.label_source})")
    print(f"Labeled pool: {len(tiers):,}  | relevant(tier>=3): {relevant:,}  | top-100 covered: {covered}/100")
    print("-" * 56)
    print(f"NDCG@10 : {ndcg10:.4f}   (weight 0.50)")
    print(f"NDCG@50 : {ndcg50:.4f}   (weight 0.30)")
    print(f"MAP     : {mapv:.4f}   (weight 0.15, tier>=3 binary)")
    print(f"P@10    : {p10:.4f}   (weight 0.05, tier>=3)")
    print("-" * 56)
    print(f"COMPOSITE: {composite:.4f}")
    print(f"top-10 tiers: {[int(t) for t in top10_tiers]}")


if __name__ == "__main__":
    main()
