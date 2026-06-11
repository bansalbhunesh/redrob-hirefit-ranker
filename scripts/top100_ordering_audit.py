#!/usr/bin/env python3
"""Full top-100 ordering audit (read-only; extends scripts/top10_ordering_audit.py).

The 2026-06-11 audit noted that 45% of the challenge composite
(0.30*NDCG@50 + 0.15*MAP) is decided at ranks 11-100, while the committed
ordering audit covered only the top 15 on NDCG@10. This study checks every
pairwise swap (i, j) within the shipped top-100 against the FULL composite
under four label sources, and reports swaps that strictly improve the
composite under ALL sources covering both ids (>= 2 covering sources, same
consensus convention as the top-15 audit).

Metric semantics match src/redrob_ranker/eval_harness.py exactly
(policy=exclude, ideal DCG over the whole label set, MAP denominator
min(total_relevant, n_scored), P@10 at tier >= 3); ideal DCGs and relevant
counts are precomputed once per source so the 4,950-swap scan is fast.

If consensus swaps exist, a greedy non-overlapping application pass estimates
the total composite available — as evidence for a hash-roll decision, never an
automatic change. submission.csv is not modified.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.eval import dcg  # noqa: E402
from redrob_ranker.eval_harness import (  # noqa: E402
    RELEVANT_TIER,
    evaluate,
    load_labels,
    load_submission,
)

SOURCES = [
    (ROOT / "artifacts" / "independent_labels_100k.jsonl", "independent"),
    (ROOT / "docs" / "llm_judge_eval_labels.jsonl", "judge1"),
    (ROOT / "docs" / "llm_judge_eval_2_labels.jsonl", "judge2"),
    (ROOT / "artifacts" / "llm_labels_expand.jsonl", "expand"),
]


class FastScorer:
    """Composite identical to eval_harness.evaluate(policy=exclude),
    with the label-set-wide constants precomputed once."""

    def __init__(self, ls):
        self.name = ls.name
        self.gains = ls.gains
        self.tiers = ls.tiers
        ideal = sorted(ls.gains.values(), reverse=True)
        self.ideal10 = dcg(ideal[:10], 10)
        self.ideal50 = dcg(ideal[:50], 50)
        self.total_relevant = sum(1 for v in ls.tiers.values() if v >= RELEVANT_TIER)

    def composite(self, ranked: list[str]) -> float:
        scored = [c for c in ranked if c in self.tiers]
        g = [self.gains[c] for c in scored]
        ndcg10 = dcg(g[:10], 10) / self.ideal10 if self.ideal10 > 0 else 0.0
        ndcg50 = dcg(g[:50], 50) / self.ideal50 if self.ideal50 > 0 else 0.0
        hits = 0
        psum = 0.0
        for i, c in enumerate(scored, start=1):
            if self.tiers[c] >= RELEVANT_TIER:
                hits += 1
                psum += hits / i
        denom = min(self.total_relevant, len(scored)) if scored else self.total_relevant
        mapv = psum / denom if denom else 0.0
        p10 = (sum(1 for c in scored[:10] if self.tiers[c] >= RELEVANT_TIER) / 10
               if scored else 0.0)
        return 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * mapv + 0.05 * p10


def main() -> None:
    shipped = load_submission(ROOT / "submission.csv")
    label_sets = [load_labels(p, name) for p, name in SOURCES if p.exists()]
    scorers = [FastScorer(ls) for ls in label_sets]

    print("shipped composite by source (policy=exclude):")
    base = {}
    for ls, sc in zip(label_sets, scorers):
        ref = evaluate(shipped, ls, unlabeled="exclude").composite
        fast = sc.composite(shipped)
        assert abs(ref - fast) < 1e-9, f"FastScorer mismatch on {sc.name}"
        base[sc.name] = fast
        cov = sum(1 for c in shipped if c in sc.tiers) / len(shipped)
        print(f"  {sc.name:<12} composite={fast:.4f} coverage={cov:.1%}")

    print("\npairwise swaps improving the composite under ALL covering sources"
          " (>=2 covering):")
    consensus: list[tuple[float, int, int]] = []
    for i, j in combinations(range(100), 2):
        a, b = shipped[i], shipped[j]
        covering = [sc for sc in scorers if a in sc.tiers and b in sc.tiers]
        if len(covering) < 2:
            continue
        if all(sc.gains.get(a) == sc.gains.get(b) and sc.tiers.get(a) == sc.tiers.get(b)
               for sc in covering):
            continue
        swapped = list(shipped)
        swapped[i], swapped[j] = swapped[j], swapped[i]
        deltas = []
        ok = True
        for sc in covering:
            d = sc.composite(swapped) - base[sc.name]
            if d <= 1e-12:
                ok = False
                break
            deltas.append(d)
        if ok:
            mean_d = sum(deltas) / len(deltas)
            consensus.append((mean_d, i, j))
            print(f"  ranks {i + 1:>3}<->{j + 1:>3}  {a} <-> {b}  "
                  f"mean delta +{mean_d:.4f}  ({len(covering)} sources)")

    if not consensus:
        print("  none — no cross-source consensus for any top-100 reorder; "
              "the freeze holds at full depth, not just top-15")
        return

    consensus.sort(reverse=True)
    used: set[int] = set()
    applied = list(shipped)
    n_applied = 0
    for _, i, j in consensus:
        if i in used or j in used:
            continue
        applied[i], applied[j] = applied[j], applied[i]
        used.update((i, j))
        n_applied += 1
    print(f"\ngreedy non-overlapping application of {n_applied} swap(s):")
    for sc in scorers:
        d = sc.composite(applied) - base[sc.name]
        print(f"  {sc.name:<12} composite delta {d:+.4f}")


if __name__ == "__main__":
    main()
