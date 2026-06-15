"""Correlation-aware weighted RRF (Direction 2). Weight each channel by its UNIQUE
information (1 - max rank-correlation with the other channels) and add an Exp4Fuse-style
co-occurrence bonus, vs equal-weight RRF. Tests whether down-weighting correlated channels
and up-weighting complementary ones yields a holdout-robust gain over plain RRF.
"""
import hashlib
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels  # noqa: E402
from exp_constrained_fusion import CHANNELS, channel_ranks  # noqa: E402
from redrob_ranker.eval_harness import LabelSet, evaluate  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402


def comp(ids, ls):
    return evaluate(ids, ls).composite


def main():
    recs, base_ids = load_pool()
    full, _, _ = labels()
    cids = [r["cid"] for r in recs]
    ranks = channel_ranks(recs)
    chans = list(CHANNELS)

    # rank vectors per channel
    rv = {ch: np.array([ranks[ch][c] for c in cids]) for ch in chans}
    # correlation matrix + unique-information weight
    print("channel rank-correlation (Spearman):")
    print("        " + "".join(f"{c[:7]:>9}" for c in chans))
    corr = np.eye(len(chans))
    for i, a in enumerate(chans):
        row = []
        for j, b in enumerate(chans):
            corr[i, j] = 1.0 if i == j else spearmanr(rv[a], rv[b]).correlation
            row.append(corr[i, j])
        print(f"{a[:7]:<8}" + "".join(f"{x:>9.2f}" for x in row))
    uniq = {chans[i]: 1.0 - max(abs(corr[i, j]) for j in range(len(chans)) if j != i)
            for i in range(len(chans))}
    tot = sum(uniq.values())
    w = {c: uniq[c] / tot for c in chans}
    print("\nunique-information weights:", {c: round(w[c], 3) for c in chans})

    K = 30
    def fuse(weighted, cobonus):
        n = {c: sum(1 for ch in chans if ranks[ch][c] <= 100) for c in cids}
        out = {}
        for c in cids:
            s = 0.0
            for ch in chans:
                wi = w[ch] if weighted else 1.0
                bonus = (n[c] / 10.0) if cobonus else 0.0
                s += (wi + bonus) / (K + ranks[ch][c])
            out[c] = s
        order = sorted(cids, key=lambda c: (-out[c], c))
        return order[:100]

    def nested(ids, R=20):
        ds = []
        for s in range(R):
            te = {c: v for c, v in full.tiers.items()
                  if int(hashlib.md5((c + "|" + str(s)).encode()).hexdigest(), 16) % 2}
            TE = LabelSet("te", te, {c: full.gains[c] for c in te})
            ds.append(comp(ids, TE) - comp(base_ids, TE))
        a = np.array(ds)
        return a.mean(), int((a > 0).sum())

    g = comp(base_ids, full)
    print(f"\ngolden composite: {g:.4f}")
    for label, wtd, cob in [("equal RRF", False, False), ("weighted RRF", True, False),
                            ("weighted RRF + co-occ", True, True)]:
        ids = fuse(wtd, cob)
        m, pos = nested(ids)
        print(f"{label:<24} full {comp(ids, full):.4f} ({comp(ids, full)-g:+.4f})  nested mean {m:+.4f} pos {pos}/20")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
