"""Two honesty audits the user flagged (Exp 6 + Exp 8):

  JUDGE-DEPENDENCE: "fusion-raw beats golden on 7/7 label sets" may overstate the
  evidence if those judges are correlated. Compute pairwise rank-correlation of the
  label families and the EFFECTIVE number of independent judges (eigenvalue
  participation ratio). If N_eff ~ 2, 7/7 is really ~2 independent votes.

  INFLUENCE / DELETION: is the +0.0128 fusion gain carried by a few promoted
  candidates? Remove each added candidate (backfill from the pool) and measure the
  gain; report max single-candidate and top-5 influence, gain without anachronism
  (fusion-clean), and bootstrap positivity.
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels  # noqa: E402
from exp_rankfusion import rankings as build_rankings  # noqa: E402
from exp_rankfusion_guarded import build_top  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

LAB = Path("C:/Users/bhune/india-runs-compare-lab/artifacts")
SETS = ["h2_availblind_labels", "merged_j1", "merged_j2", "merged_j3",
        "relabel_j4", "relabel_g25", "blind_test_frozen"]


def comp(ids, ls):
    return evaluate(ids, ls).composite


def judge_dependence():
    sets = {}
    for n in SETS:
        p = LAB / f"{n}.jsonl"
        if p.exists():
            sets[n] = load_labels(p)
    names = list(sets)
    C = np.eye(len(names))
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = sets[names[i]].gains, sets[names[j]].gains
            common = list(set(a) & set(b))
            if len(common) < 20:
                r = np.nan
            else:
                r = spearmanr([a[c] for c in common], [b[c] for c in common]).correlation
            C[i, j] = C[j, i] = (r if r == r else 0.0)
    print("== judge-dependence: pairwise Spearman of label gains ==")
    print("       " + "".join(f"{n[:7]:>8}" for n in names))
    for i, n in enumerate(names):
        print(f"{n[:7]:<7}" + "".join(f"{C[i, j]:>8.2f}" for j in range(len(names))))
    ev = np.linalg.eigvalsh(C)
    ev = ev[ev > 0]
    n_eff = (ev.sum() ** 2) / (np.square(ev).sum())
    mean_off = (C.sum() - len(names)) / (len(names) * (len(names) - 1))
    print(f"\nmean off-diagonal correlation: {mean_off:.2f}")
    print(f"EFFECTIVE independent judges (eigenvalue participation ratio): {n_eff:.2f} of {len(names)}")
    print("-> '7/7 improved' is really ~%.1f independent votes." % n_eff)


def influence():
    recs, base_ids = load_pool()
    full, _, _ = labels()
    ranks = build_rankings(recs)
    fusion = build_top(recs, ranks, "raw")
    clean = build_top(recs, ranks, "clean")
    base_set, fus_set = set(base_ids), set(fusion)
    pool_ids = [r["cid"] for r in recs]
    g0 = comp(base_ids, full)
    f0 = comp(fusion, full)
    gain = f0 - g0
    print("\n== influence / deletion on the +%.4f fusion gain ==" % gain)
    added = [c for c in fusion if c not in base_set]
    # marginal influence: drop each added cand from fusion, backfill next pool cand
    backfill = [c for c in pool_ids if c not in fus_set][0]
    infl = []
    for c in added:
        alt = [x for x in fusion if x != c] + [backfill]
        infl.append((c, f0 - comp(alt[:100], full)))
    infl.sort(key=lambda t: -t[1])
    max1 = infl[0][1] if infl else 0.0
    top5 = sum(d for _, d in infl[:5])
    print(f"added candidates: {len(added)}")
    print(f"max single-candidate influence on gain: {max1:+.4f}  ({100*max1/gain:.0f}% of the gain)")
    print(f"top-5 candidate influence:              {top5:+.4f}  ({100*top5/gain:.0f}% of the gain)")
    print(f"gain WITHOUT anachronism (fusion-clean): {comp(clean, full)-g0:+.4f}")
    # bootstrap positivity
    import hashlib
    from redrob_ranker.eval_harness import LabelSet
    pos = 0
    for s in range(50):
        te = {c: v for c, v in full.tiers.items()
              if int(hashlib.md5((c + "|" + str(s)).encode()).hexdigest(), 16) % 2}
        TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        pos += comp(fusion, TE) > comp(base_ids, TE)
    print(f"bootstrap R=50: fusion>golden in {pos}/50")


def main():
    judge_dependence()
    influence()


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
