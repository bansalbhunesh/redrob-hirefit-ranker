"""Non-circular check: do INDEPENDENT LLM-judge label sets penalize the anachronism
honeypots that inflate the blind proxy? The human-aligned sweep was partly circular
(its penalty used our own detector). The merged_j*/relabel_j*/blind_test_frozen sets
were graded by different judge models, not our detector -- so if honeypot-free clean
fusion does relatively better on THEM than on the blind proxy, that is independent
evidence the honeypots are genuinely low-quality, not just flagged-by-us.

Reports composite (and coverage) for golden / fusion-raw / fusion-guard / fusion-clean
on every available label set. unlabeled='exclude' (sets are small; score only labeled).
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")

from _lib import load_pool  # noqa: E402
from exp_rankfusion import rankings as build_rankings  # noqa: E402
from exp_rankfusion_guarded import build_top  # noqa: E402
from redrob_ranker.eval_harness import load_labels, evaluate  # noqa: E402

LAB = Path("C:/Users/bhune/india-runs-compare-lab/artifacts")
SETS = ["h2_availblind_labels", "blind_test_frozen",
        "merged_j1", "merged_j2", "merged_j3",
        "relabel_j1", "relabel_j2", "relabel_j3", "relabel_j4", "relabel_g25"]


def main():
    recs, base_ids = load_pool()
    ranks = build_rankings(recs)
    R = {
        "golden": list(base_ids),
        "fusion-raw": build_top(recs, ranks, "raw"),
        "fusion-guard": build_top(recs, ranks, "guarded"),
        "fusion-clean": build_top(recs, ranks, "clean"),
    }
    print(f"{'label set':<22}{'n':>6}  " + "".join(f"{k:>13}" for k in R) + "   cov   clean-raw")
    clean_gt_golden = clean_gt_raw = usable = 0
    MIN_COV = 0.50  # a set with little overlap with golden's top-100 is uninformative
    for name in SETS:
        p = LAB / f"{name}.jsonl"
        if not p.exists():
            continue
        try:
            ls = load_labels(p)
        except Exception as e:
            print(f"{name:<22} LOAD_FAIL {e}")
            continue
        comps, covs = {}, {}
        for k, ids in R.items():
            ev = evaluate(ids, ls, unlabeled="exclude")
            comps[k], covs[k] = ev.composite, ev.coverage
        cov = covs["golden"]
        skip = "  (SKIP low-cov)" if cov < MIN_COV else ""
        row = "".join(f"{comps[k]:>13.4f}" for k in R)
        c_r = comps["fusion-clean"] - comps["fusion-raw"]
        print(f"{name:<22}{len(ls.tiers):>6}  {row}   {cov*100:>3.0f}% {c_r:>+8.4f}{skip}")
        if cov < MIN_COV:
            continue
        usable += 1
        clean_gt_golden += comps["fusion-clean"] > comps["golden"] + 1e-4
        clean_gt_raw += c_r > 1e-4
    print(f"\nusable sets (golden cov >= {MIN_COV:.0%}): {usable}")
    print(f"  fusion-clean (honeypot-free) > golden:      {clean_gt_golden}/{usable}")
    print(f"  fusion-clean > fusion-raw (=judges penalize honeypots): {clean_gt_raw}/{usable}")
    print("  -> if the second number is ~0, independent judges do NOT penalize the")
    print("     anachronism honeypots; the integrity hedge needs MANUAL human date-checks.")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
