"""Is there any CLEAN rank-fusion gain, or is the whole gain honeypot re-promotion?

The raw RRF tail-fusion gains +0.0128 composite on the blind proxy, but the diagnostic
showed 25/39 promotions are anachronism honeypots and several are JD-disqualified
profiles that the hand pipeline's multiplicative guardrails deliberately demoted. RRF
over the 5 RAW feature families ignores those guardrails. This script re-tests three
variants of the modal config (all-families, K=30, top-lock=20):

  RAW      : fuse raw family ranks (reproduces the proxy gain)
  GUARDED  : multiply the fused score by honeypot_mult * disq_mult  (guardrails reassert)
  CLEAN    : same as GUARDED, but also forbid promoting anachronism-flagged candidates

If GUARDED/CLEAN still gain -> a real, shippable, novel rank-space improvement.
If the gain collapses -> the entire fusion 'win' was the proxy-inflation trap, and this
is measured negative #13 (rank fusion), strengthening the proxy-inflation thesis.
"""
import hashlib
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels  # noqa: E402
from exp_rankfusion import FAMILIES, rankings  # noqa: E402
from redrob_ranker.eval_harness import LabelSet, evaluate  # noqa: E402

try:
    from anachronism import is_anachronistic
except Exception:
    is_anachronistic = None


def comp(ids, ls):
    return evaluate(ids, ls).composite


def build_top(recs, ranks, mode, K=30, lock=20, k=100):
    cids = [r["cid"] for r in recs]
    rec_by = {r["cid"]: r for r in recs}
    hand = np.array([r["hand"] for r in recs], dtype=float)
    fams = list(FAMILIES)
    fused = np.array(
        [sum(1.0 / (K + ranks[f][c]) for f in fams) for c in cids], dtype=float)
    if mode in ("guarded", "clean"):
        guard = np.array([rec_by[c]["honeypot_mult"] * rec_by[c]["disq_mult"] for c in cids])
        fused = fused * guard
    forbid = set()
    if mode == "clean" and is_anachronistic:
        forbid = {c for c in cids if rec_by[c].get("cand") and is_anachronistic(rec_by[c]["cand"])}
    # top-lock the hand top-`lock`, fill the rest by fused (skipping forbidden for 'clean')
    hand_order = sorted(range(len(cids)), key=lambda i: (-hand[i], cids[i]))
    locked = [cids[i] for i in hand_order[:lock]]
    locked_set = set(locked)
    rest = [i for i in range(len(cids)) if cids[i] not in locked_set and cids[i] not in forbid]
    rest.sort(key=lambda i: (-fused[i], cids[i]))
    return (locked + [cids[i] for i in rest])[:k]


def nested(recs, base_ids, ranks, mode, R=20):
    full, _, _ = labels()
    top = build_top(recs, ranks, mode)
    deltas = []
    for s in range(R):
        te = {c: v for c, v in full.tiers.items()
              if int(hashlib.md5((c + "|" + str(s)).encode()).hexdigest(), 16) % 2}
        TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        deltas.append(comp(top, TE) - comp(base_ids, TE))
    return np.array(deltas), top


def main():
    recs, base_ids = load_pool()
    full, _, _ = labels()
    ranks = rankings(recs)
    rec_by = {r["cid"]: r for r in recs}
    base_set = set(base_ids)
    bf = comp(base_ids, full)
    print(f"golden baseline (full): {bf:.4f}\n")
    print(f"{'variant':<10}{'full':>9}{'d-full':>9}   repeated-holdout (R=20)")
    for mode in ("raw", "guarded", "clean"):
        a, top = nested(recs, base_ids, ranks, mode)
        ff = comp(top, full)
        added = [c for c in top if c not in base_set]
        n_anach = sum(1 for c in added if is_anachronistic and rec_by[c].get("cand")
                      and is_anachronistic(rec_by[c]["cand"]))
        n_disq = sum(1 for c in added if rec_by[c]["disq_mult"] < 1.0)
        print(f"{mode:<10}{ff:>9.4f}{ff - bf:>+9.4f}   mean {a.mean():+.4f} std {a.std():.4f} "
              f"pos {int((a > 0).sum())}/20  | adds={len(added)} anach={n_anach} disq={n_disq}")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
