"""Learned stacking meta-model — let the labels weight the aggregators.

Equal-weight meta-fusion tied Copeland. This instead FITS a linear stacker on the train-label
half: target = blind tier, features = the 5 base-method scores (hand, RRF, Borda, MC4, Copeland),
solved by least squares. The learned weights are the data's own opinion of how to mix the methods.
Rank by the stacker's prediction, top-lock, and gate with the nested R=20 discipline (a learned
combiner is the textbook way to overfit a proxy, so the honest out-of-sample test is decisive).
Golden untouched.
"""
import hashlib
import sys
from collections import Counter

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from _lib import labels, load_pool  # noqa: E402
from exp_rankfusion import FAMILIES, comp, fuse_topk, rankings, rrf_scores, borda_scores  # noqa: E402
from exp_rank_ensemble import copeland as copeland_g, mc4 as mc4_g  # noqa: E402
from redrob_ranker.eval_harness import LabelSet  # noqa: E402


def _z(x):
    x = np.asarray(x, float); s = x.std()
    return (x - x.mean()) / s if s > 0 else x * 0.0


def main():
    recs, base_ids = load_pool()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    fr = rankings(recs); fams = list(FAMILIES); eq = {f: 1.0 for f in fams}
    feats = np.column_stack([
        _z(hand),
        _z(rrf_scores(cids, fr, fams, eq, 30)),
        _z(borda_scores(cids, fr, fams, eq, len(cids))),
        _z(mc4_g(cids, fr, fams)),
        _z(copeland_g(cids, fr, fams)),
    ])
    names = ["hand", "rrf", "borda", "mc4", "copeland"]
    full, train, test = labels()
    idx = {c: i for i, c in enumerate(cids)}

    # Fit linear stacker on the train-label half (candidates in the pool with a train tier).
    tr_rows = [(idx[c], full.tiers[c]) for c in train.tiers if c in idx]
    A = np.column_stack([feats[[i for i, _ in tr_rows]], np.ones(len(tr_rows))])
    y = np.array([t for _, t in tr_rows], float)
    w, *_ = np.linalg.lstsq(A, y, rcond=None)
    print("learned stacker weights:")
    for n, wi in zip(names + ["bias"], w):
        print(f"  {n:<10}{wi:+.4f}")
    pred = feats @ w[:-1] + w[-1]

    base_te = comp(base_ids, test)
    configs = [(f"stack lock{l}", fuse_topk(recs, pred, hand, l)) for l in (0, 10, 20, 30)]
    configs.append(("ref Copeland lock30", fuse_topk(recs, feats[:, 4], hand, 30)))
    print(f"\nbaseline golden: full={comp(base_ids, full):.4f} test={base_te:.4f}\n")
    print(f'{"config":<22}{"full":>9}{"train":>9}{"test":>9}{"t-base":>9}')
    tops = {}
    for name, ids in configs:
        tops[name] = ids
        f, tr, te = comp(ids, full), comp(ids, train), comp(ids, test)
        print(f"{name:<22}{f:>9.4f}{tr:>9.4f}{te:>9.4f}{te - base_te:>+9.4f}")

    deltas, picks = [], []
    for s in range(20):
        tr, te = {}, {}
        for cc, v in full.tiers.items():
            (te if int(hashlib.md5((cc + "|" + str(s)).encode()).hexdigest(), 16) % 2 else tr)[cc] = v
        TR = LabelSet("tr", tr, {c: full.gains[c] for c in tr}); TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        best = max(configs, key=lambda c: comp(tops[c[0]], TR))
        deltas.append(comp(tops[best[0]], TE) - comp(base_ids, TE)); picks.append(best[0])
    a = np.array(deltas)
    print(f"\nNESTED R=20: mean {a.mean():+.4f} std {a.std():.4f} pos {int((a>0).sum())}/20 "
          f"min {a.min():+.4f} max {a.max():+.4f}")
    for nm, ct in Counter(picks).most_common():
        print(f"  {ct:>2}x  {nm}")
    print(f"\nbest full composite: {max(comp(ids, full) for _, ids in configs):.4f}  | champion Copeland=0.8779")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
