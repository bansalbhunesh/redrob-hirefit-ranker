"""Condorcet-family rank aggregation — Copeland and local Kemenization.

Continues the obscure-aggregator hunt (after MC4 / Plackett-Luce). Two more methods the
field rarely uses, both over the same 6 ranker families, same arbiter, same discipline:

  1. Copeland: score(c) = (# candidates c beats by family-majority) − (# that beat c).
     The classic Condorcet tournament score.
  2. Local Kemenization (Dwork et al. WWW 2001): seed with an order, then repeatedly swap
     adjacent pairs whenever the family-majority disagrees with their seed order. Converges
     to a local optimum of Kendall-tau distance to the majority preference — a cheap
     approximation to the NP-hard Kemeny-optimal consensus. Seeded from MC4 and from hand.

Exact Schulze / Kemeny are O(N^3)/NP-hard and infeasible on the 3000-pool; local
Kemenization is the scalable, deterministic stand-in. Golden untouched.
"""
import hashlib
import sys
from collections import Counter

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from _lib import labels, load_pool  # noqa: E402
from exp_rankfusion import FAMILIES, comp, fuse_topk, rankings  # noqa: E402
from exp_rank_markov import _rank_arrays, mc4_scores  # noqa: E402
from redrob_ranker.eval_harness import LabelSet  # noqa: E402


def _beats(cids, ranks, fams):
    """beats[c,d] = # families that rank d strictly above c (lower rank = better)."""
    ra = _rank_arrays(cids, ranks)
    N = len(cids)
    beats = np.zeros((N, N), dtype=np.int16)
    for f in fams:
        r = ra[f]
        beats += (r[None, :] < r[:, None]).astype(np.int16)
    return beats


def copeland_scores(cids, ranks, fams):
    beats = _beats(cids, ranks, fams)
    thr = len(fams) // 2 + 1
    maj_dc = beats >= thr               # maj_dc[c,d]=1 if majority prefers d over c
    loses = maj_dc.sum(axis=1)          # # d that beat c
    wins = maj_dc.sum(axis=0)           # # c... = # candidates that c beats (col sum)
    return (wins - loses).astype(float)


def local_kemeny(cids, ranks, fams, seed_order, passes=40):
    """seed_order: list of indices best->worst. Bubble adjacent pairs by family-majority."""
    beats = _beats(cids, ranks, fams)
    thr = len(fams) // 2 + 1
    order = list(seed_order)
    for _ in range(passes):
        swapped = False
        for i in range(len(order) - 1):
            a, b = order[i], order[i + 1]
            # if majority prefers b over a (beats[a,b] >= thr), b should rank higher
            if beats[a, b] >= thr and beats[b, a] < thr:
                order[i], order[i + 1] = b, a
                swapped = True
        if not swapped:
            break
    N = len(order)
    fused = np.empty(N)
    for pos, idx in enumerate(order):
        fused[idx] = N - pos                # higher = better
    return fused


def gate(recs, base_ids, configs):
    full, train, test = labels()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    base_f, base_tr, base_te = comp(base_ids, full), comp(base_ids, train), comp(base_ids, test)
    print(f"baseline: full={base_f:.4f} train={base_tr:.4f} test={base_te:.4f}\n")
    print(f'{"config":<40}{"full":>9}{"train":>9}{"test":>9}{"t-base":>9}')
    rows, tops = [], {}
    for name, fused, lock in configs:
        top = fuse_topk(recs, fused, hand, lock)
        tops[name] = top
        f, tr, te = comp(top, full), comp(top, train), comp(top, test)
        rows.append((name, f, tr, te, te - base_te));
        print(f"{name:<40}{f:>9.4f}{tr:>9.4f}{te:>9.4f}{te - base_te:>+9.4f}")
    best = max(rows, key=lambda r: r[2])
    print(f"\ntrain-best: {best[0]}  ->  HOLDOUT delta {best[3] - base_te:+.4f}")
    return base_f, rows, tops


def nested(recs, base_ids, configs, tops, R=20):
    full, _, _ = labels()
    deltas, picks = [], []
    for s in range(R):
        tr, te = {}, {}
        for cc, v in full.tiers.items():
            (te if int(hashlib.md5((cc + "|" + str(s)).encode()).hexdigest(), 16) % 2 else tr)[cc] = v
        TR = LabelSet("tr", tr, {c: full.gains[c] for c in tr})
        TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        best = max(configs, key=lambda c: comp(tops[c[0]], TR))
        deltas.append(comp(tops[best[0]], TE) - comp(base_ids, TE))
        picks.append(best[0])
    a = np.array(deltas)
    print(f"\nNESTED R={R}: mean {a.mean():+.4f} std {a.std():.4f} pos {int((a>0).sum())}/{R} "
          f"min {a.min():+.4f} max {a.max():+.4f}")
    for nm, ct in Counter(picks).most_common():
        print(f"  {ct:>2}x  {nm}")
    return a


def main():
    recs, base_ids = load_pool()
    ranks = rankings(recs)
    cids = [r["cid"] for r in recs]
    fams = list(FAMILIES)
    hand = np.array([r["hand"] for r in recs], dtype=float)

    print("Copeland ...")
    cope = copeland_scores(cids, ranks, fams)
    print("local Kemenization (seed=MC4) ...")
    mc4 = mc4_scores(cids, ranks, fams)
    mc4_order = sorted(range(len(cids)), key=lambda i: (-mc4[i], cids[i]))
    kem_mc4 = local_kemeny(cids, ranks, fams, mc4_order)
    print("local Kemenization (seed=hand) ...")
    hand_order = sorted(range(len(cids)), key=lambda i: (-hand[i], cids[i]))
    kem_hand = local_kemeny(cids, ranks, fams, hand_order)

    configs = []
    for lock in (0, 10, 20, 30):
        configs.append((f"Copeland lock{lock}", cope, lock))
        configs.append((f"Kemeny(MC4) lock{lock}", kem_mc4, lock))
        configs.append((f"Kemeny(hand) lock{lock}", kem_hand, lock))

    print("\n" + "=" * 74)
    print("CONDORCET-FAMILY GATE (train-select, holdout-report)")
    print("=" * 74)
    base_f, rows, tops = gate(recs, base_ids, configs)
    print("\n" + "=" * 74)
    print("NESTED REPEATED HOLDOUT (R=20)")
    print("=" * 74)
    nested(recs, base_ids, configs, tops, R=20)
    print(f"\nbest full-set composite: {max(r[1] for r in rows):.4f}  (baseline {base_f:.4f})")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
