"""Minimax-robust ranking across all 7 known label sets.

Every prior method optimized ONE arbiter (the blind set). But the win probability is governed by
how the UNKNOWN hidden labels behave. The principled hedge: pick the ranking with the best
WORST-CASE composite across all 7 independent evaluators we have (blind arbiter + 6 LLM-judge
sets) — a proxy for "robust to whatever the 8th, hidden evaluator is." This is the real
best-of-best for an unknown judge, not the best-on-one-proxy.

Compares golden, fusion-raw, Copeland, MC4, and the meta/banded configs by their min / mean /
spread across the 7 sets, and reports the max-min (minimax-optimal) ranking. Golden untouched.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from _lib import load_pool  # noqa: E402
from exp_rankfusion import FAMILIES, fuse_topk, rankings, rrf_scores, borda_scores  # noqa: E402
from exp_rank_ensemble import copeland as copeland_g, mc4 as mc4_g  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402

LAB = Path("C:/Users/bhune/india-runs-compare-lab/artifacts")
SETS = ["h2_availblind_labels", "merged_j1", "merged_j2", "merged_j3",
        "relabel_j4", "relabel_g25", "blind_test_frozen"]


def main():
    recs, base_ids = load_pool()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    fr = rankings(recs); fams = list(FAMILIES); eq = {f: 1.0 for f in fams}
    cope = copeland_g(cids, fr, fams)
    m4 = mc4_g(cids, fr, fams)
    rrf = rrf_scores(cids, fr, fams, eq, 30)

    fusion_raw = [r["candidate_id"] for r in csv.DictReader(open("experiments/fusion_raw_submission.csv"))][:100]
    candidates = {
        "golden": base_ids,
        "fusion-raw": fusion_raw,
        "Copeland lock20": fuse_topk(recs, cope, hand, 20),
        "Copeland lock30": fuse_topk(recs, cope, hand, 30),
        "MC4 lock20": fuse_topk(recs, m4, hand, 20),
        "MC4 lock30": fuse_topk(recs, m4, hand, 30),
        "RRF lock30": fuse_topk(recs, rrf, hand, 30),
    }

    labelsets = {}
    for n in SETS:
        p = LAB / f"{n}.jsonl"
        if p.exists():
            labelsets[n] = load_labels(p)
    names = list(labelsets)

    print(f"composite across {len(names)} label sets\n")
    print(f'{"ranking":<18}' + "".join(f"{n[:10]:>11}" for n in names) + f'{"MIN":>9}{"MEAN":>9}')
    table = {}
    for rk, ids in candidates.items():
        comps = [evaluate(ids, labelsets[n]).composite for n in names]
        table[rk] = comps
        print(f"{rk:<18}" + "".join(f"{c:>11.4f}" for c in comps) + f"{min(comps):>9.4f}{np.mean(comps):>9.4f}")

    best_min = max(candidates, key=lambda r: min(table[r]))
    best_mean = max(candidates, key=lambda r: np.mean(table[r]))
    print(f"\nMINIMAX-optimal (best worst-case across all 7 evaluators): {best_min}  "
          f"(min={min(table[best_min]):.4f})")
    print(f"MEAN-optimal: {best_mean}  (mean={np.mean(table[best_mean]):.4f})")
    print("\nInterpretation: the max-min ranking is the safest bet against an unknown hidden")
    print("evaluator; the mean-optimal is the best if the hidden labels resemble the average judge.")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
