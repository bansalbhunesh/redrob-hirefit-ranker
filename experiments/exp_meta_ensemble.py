"""Best-of-best meta-ensemble: mix the strongest rankers, take each one's best part.

Three constructions over the five base rankings (hand, RRF, Borda, MC4, Copeland), all
holdout/nested-gated against the frozen blind arbiter; golden untouched:

  1. META-AGGREGATION — treat the 5 method rankings as voters and aggregate THEM
     (meta-RRF / meta-Borda / meta-Copeland). A consensus of consensuses.
  2. BANDED HYBRID — use the empirically-best method per rank band: hand for the locked
     top (P@10=1.0, NDCG@10), Copeland for the 11-50 tail (best NDCG@50), MC4 for 51-100.
     Literally "take each method's best part."
  3. RANK-AVERAGE — mean of the 5 methods' rank positions (a simple robust blend).

Champion to beat: Copeland lock30 = 0.8779 full, nested +0.0142 (19/20).
"""
import hashlib
import sys
from collections import Counter

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from _lib import labels, load_pool  # noqa: E402
from exp_rankfusion import FAMILIES, comp, fuse_topk, rankings, rrf_scores, borda_scores  # noqa: E402
from exp_rank_ensemble import copeland as copeland_g, mc4 as mc4_g  # generic over passed fams  # noqa: E402
from redrob_ranker.eval_harness import LabelSet  # noqa: E402


def _order_from_scores(cids, scores):
    return sorted(range(len(cids)), key=lambda i: (-scores[i], cids[i]))


def _ranks_from_order(cids, order):
    d = {}
    for pos, i in enumerate(order):
        d[cids[i]] = pos + 1
    return d


def main():
    recs, base_ids = load_pool()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    fr = rankings(recs)                       # the 6 family rankings
    famnames = list(FAMILIES)
    eq = {f: 1.0 for f in famnames}

    # --- 5 base method scores over the full pool ---
    base = {
        "hand": hand,
        "rrf": rrf_scores(cids, fr, famnames, eq, 30),
        "borda": borda_scores(cids, fr, famnames, eq, len(cids)),
        "mc4": mc4_g(cids, fr, famnames),
        "copeland": copeland_g(cids, fr, famnames),
    }
    methods = list(base)
    # method full-pool rankings -> treat as voters
    meta_ranks = {m: _ranks_from_order(cids, _order_from_scores(cids, base[m])) for m in methods}

    # --- 1. meta-aggregation over the method rankings ---
    meta_rrf = rrf_scores(cids, meta_ranks, methods, {m: 1.0 for m in methods}, 30)
    meta_borda = borda_scores(cids, meta_ranks, methods, {m: 1.0 for m in methods}, len(cids))
    meta_cope = copeland_g(cids, meta_ranks, methods)
    meta_mc4 = mc4_g(cids, meta_ranks, methods)
    # rank-average (lower mean rank = better -> negate)
    rank_avg = -np.array([np.mean([meta_ranks[m][c] for m in methods]) for c in cids])

    # --- 2. banded hybrid: hand lock / Copeland 11-50 / MC4 51-100 ---
    def banded(lock):
        order_c = _order_from_scores(cids, base["copeland"])
        order_m = _order_from_scores(cids, base["mc4"])
        hand_order = _order_from_scores(cids, hand)
        picked, seen = [], set()
        for i in hand_order[:lock]:
            picked.append(cids[i]); seen.add(cids[i])
        for i in order_c:                      # fill 11..50 by Copeland
            if len(picked) >= 50:
                break
            if cids[i] not in seen:
                picked.append(cids[i]); seen.add(cids[i])
        for i in order_m:                      # fill 51..100 by MC4
            if len(picked) >= 100:
                break
            if cids[i] not in seen:
                picked.append(cids[i]); seen.add(cids[i])
        return picked[:100]

    configs = []
    for lock in (20, 30):
        configs.append((f"meta-RRF lock{lock}", fuse_topk(recs, meta_rrf, hand, lock)))
        configs.append((f"meta-Copeland lock{lock}", fuse_topk(recs, meta_cope, hand, lock)))
        configs.append((f"meta-MC4 lock{lock}", fuse_topk(recs, meta_mc4, hand, lock)))
        configs.append((f"meta-Borda lock{lock}", fuse_topk(recs, meta_borda, hand, lock)))
        configs.append((f"rank-avg lock{lock}", fuse_topk(recs, rank_avg, hand, lock)))
    for lock in (10, 20, 30):
        configs.append((f"BANDED hand/cope/mc4 lock{lock}", banded(lock)))
    # reference: pure Copeland lock30 (the current champion)
    configs.append(("ref Copeland lock30", fuse_topk(recs, base["copeland"], hand, 30)))

    full, train, test = labels()
    base_te = comp(base_ids, test)
    print(f"baseline golden: full={comp(base_ids, full):.4f} test={base_te:.4f}\n")
    print(f'{"config":<34}{"full":>9}{"train":>9}{"test":>9}{"t-base":>9}')
    tops = {}
    for name, ids in configs:
        tops[name] = ids
        f, tr, te = comp(ids, full), comp(ids, train), comp(ids, test)
        print(f"{name:<34}{f:>9.4f}{tr:>9.4f}{te:>9.4f}{te - base_te:>+9.4f}")

    deltas, picks = [], []
    R = 20
    for s in range(R):
        tr, te = {}, {}
        for cc, v in full.tiers.items():
            (te if int(hashlib.md5((cc + "|" + str(s)).encode()).hexdigest(), 16) % 2 else tr)[cc] = v
        TR = LabelSet("tr", tr, {c: full.gains[c] for c in tr}); TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        best = max(configs, key=lambda c: comp(tops[c[0]], TR))
        deltas.append(comp(tops[best[0]], TE) - comp(base_ids, TE)); picks.append(best[0])
    a = np.array(deltas)
    print(f"\nNESTED R={R}: mean {a.mean():+.4f} std {a.std():.4f} pos {int((a>0).sum())}/{R} "
          f"min {a.min():+.4f} max {a.max():+.4f}")
    for nm, ct in Counter(picks).most_common():
        print(f"  {ct:>2}x  {nm}")
    bestfull = max((comp(ids, full), name) for name, ids in configs)
    print(f"\nbest full composite: {bestfull[0]:.4f}  ({bestfull[1]})  | champion Copeland=0.8779")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
