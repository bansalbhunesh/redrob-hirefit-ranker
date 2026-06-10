#!/usr/bin/env python3
"""Score a submission CSV against a labels file using the challenge composite.

Thin CLI wrapper around the shared harness (redrob_ranker.eval_harness) so all
docs report numbers from one code path. Default unlabeled policy here is
"zero" (missing labels count as relevance 0) to stay comparable with earlier
published numbers; experiments use the harness default "exclude".

Labels file: JSONL with {"candidate_id", "tier"} (0..5). Works with either
build_independent_labels.py (heuristic, non-circular) or llm_judge_labels.py.

P@10 uses tier>=3 ("relevant") per submission_spec.md section 4. MAP is binary
at tier>=3 with AP computed over the submitted ranking (documented approximation;
only relative deltas between ranker variants are meaningful here).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from redrob_ranker.eval_harness import (  # noqa: E402
    RELEVANT_TIER,
    average_precision,
    evaluate,
    load_labels,
    load_submission,
    precision_at_k,
)

# Re-exported for back-compat (tests and older notebooks import these from here).
__all__ = ["average_precision", "precision_at_k", "evaluate", "load_labels", "load_submission"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Score a submission against independent labels.")
    ap.add_argument("--submission", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--label-source", default="independent-heuristic",
                    help="Annotation for the report header (e.g. 'llm-judge').")
    ap.add_argument("--unlabeled", choices=["exclude", "zero"], default="zero",
                    help="Policy for candidates without labels (default: zero, "
                    "matching earlier published numbers).")
    args = ap.parse_args()

    ranked = load_submission(args.submission)
    labels = load_labels(args.labels, name=args.label_source)
    result = evaluate(ranked, labels, unlabeled=args.unlabeled)

    relevant = sum(1 for v in labels.tiers.values() if v >= RELEVANT_TIER)
    covered = round(result.coverage * len(ranked))
    top10_tiers = [labels.tiers.get(cid, 0.0) for cid in ranked[:10]]
    print(f"Submission : {args.submission}")
    print(f"Labels     : {args.labels}  (source: {args.label_source})")
    print(f"Labeled pool: {len(labels.tiers):,}  | relevant(tier>={int(RELEVANT_TIER)}): {relevant:,}  "
          f"| top-100 covered: {covered}/{len(ranked)}  | policy: {result.policy}")
    print("-" * 56)
    print(f"NDCG@10 : {result.ndcg10:.4f}   (weight 0.50)")
    print(f"NDCG@50 : {result.ndcg50:.4f}   (weight 0.30)")
    print(f"MAP     : {result.map:.4f}   (weight 0.15, tier>={int(RELEVANT_TIER)} binary)")
    print(f"P@10    : {result.p10:.4f}   (weight 0.05, tier>={int(RELEVANT_TIER)})")
    print("-" * 56)
    print(f"COMPOSITE: {result.composite:.4f}")
    print(f"top-10 tiers: {[int(t) for t in top10_tiers]}")


if __name__ == "__main__":
    main()
