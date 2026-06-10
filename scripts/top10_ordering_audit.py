#!/usr/bin/env python3
"""Phase-D ordering audit: is there any cross-source consensus that reordering the
shipped top-100 improves NDCG@10? Checks judge #1, judge #2, and (if present) the
expansion labels. No change is made unless ALL sources agree — and any change would
still go through the pre-registered challenger gate, never ad hoc."""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.eval_harness import _ndcg, load_labels, load_submission  # noqa: E402

SOURCES = [
    (ROOT / "docs" / "llm_judge_eval_labels.jsonl", "judge1"),
    (ROOT / "docs" / "llm_judge_eval_2_labels.jsonl", "judge2"),
    (ROOT / "artifacts" / "llm_labels_expand.jsonl", "expand"),
]


def main() -> None:
    ranked = load_submission(ROOT / "submission.csv")
    sets = [(name, load_labels(p, name)) for p, name in SOURCES if p.exists()]

    print("shipped NDCG@10 by source (top-100 ids only, exclude policy):")
    for name, ls in sets:
        scored = [c for c in ranked if c in ls.tiers]
        print(f"  {name:8s} NDCG@10={_ndcg(scored, ls.gains, 10):.4f}")

    # Exhaustive pairwise swaps within the top-15: does ANY swap improve NDCG@10
    # under EVERY source that covers both ids?
    print("\nswaps improving NDCG@10 under ALL covering sources:")
    found = 0
    for i, j in combinations(range(15), 2):
        improves_all = True
        covered = 0
        for name, ls in sets:
            if ranked[i] not in ls.tiers or ranked[j] not in ls.tiers:
                continue
            covered += 1
            base = [c for c in ranked if c in ls.tiers]
            swapped = list(ranked)
            swapped[i], swapped[j] = swapped[j], swapped[i]
            swapped = [c for c in swapped if c in ls.tiers]
            if _ndcg(swapped, ls.gains, 10) <= _ndcg(base, ls.gains, 10):
                improves_all = False
                break
        if improves_all and covered >= 2:
            found += 1
            print(f"  swap ranks {i + 1}<->{j + 1}: {ranked[i]} <-> {ranked[j]} "
                  f"(covered by {covered} sources)")
    if not found:
        print("  none — no cross-source consensus for any top-15 reorder; HOLD the freeze")


if __name__ == "__main__":
    main()
