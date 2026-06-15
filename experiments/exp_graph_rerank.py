"""Stress-test a graph-based reranker (an untested SOTA-adjacent class the field likes:
GNN-lite / graph label-propagation / 'similar candidates should score similarly').

Method: build a cosine k-NN graph over the 22 weighted feature vectors of the pool,
then smooth the hand score across neighbours -- s' = (1-a)*hand_n + a*neighbour_mean(hand_n),
one propagation step (personalized-PageRank-lite). Sweep a, choose on TRAIN, score the
untouched TEST half; confirm with nested R=20 repeated holdout. Also report the proxy-
inflation diagnostic (anachronism exposure of the produced top-100).

Hypothesis (to be tested, not assumed): graph smoothing pulls scores toward dense
regions of feature space (the most common candidate archetype), which on a saturated
proxy is either noise or mild proxy-inflation -- not a genuine ranking gain.
"""
import hashlib
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels, minmax  # noqa: E402
from anachronism import is_anachronistic  # noqa: E402
from redrob_ranker.constants import BASE_FEATURE_WEIGHTS  # noqa: E402
from redrob_ranker.eval_harness import LabelSet, evaluate  # noqa: E402

FEATS = list(BASE_FEATURE_WEIGHTS)


def main():
    recs, base_ids = load_pool()
    full, train, test = labels()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    hand_n = minmax(hand)

    # feature matrix (z-scored) and cosine k-NN graph
    X = np.array([[r["values"].get(f, 0.0) for f in FEATS] for r in recs], dtype=float)
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    k = 10
    sims = Xn @ Xn.T
    np.fill_diagonal(sims, -1.0)
    nn = np.argpartition(-sims, k, axis=1)[:, :k]
    neigh_mean = hand_n[nn].mean(axis=1)  # mean hand_n of each node's k neighbours

    def ranktop(score):
        order = sorted(range(len(cids)), key=lambda i: (-score[i], cids[i]))
        return [cids[i] for i in order[:100]]

    def comp(ids, ls):
        return evaluate(ids, ls).composite

    base_te = comp(base_ids, test)
    alphas = [0.0, 0.1, 0.2, 0.3, 0.5]
    print(f"baseline test={base_te:.4f}")
    print(f"{'alpha':>6}{'full':>9}{'train':>9}{'test':>9}{'t-base':>9}")
    rows = []
    for a in alphas:
        s = (1 - a) * hand_n + a * neigh_mean
        top = ranktop(s)
        rows.append((a, comp(top, full), comp(top, train), comp(top, test), top))
        print(f"{a:>6.1f}{rows[-1][1]:>9.4f}{rows[-1][2]:>9.4f}{rows[-1][3]:>9.4f}{rows[-1][3]-base_te:>+9.4f}")
    best = max(rows, key=lambda r: r[2])
    print(f"train-best alpha={best[0]} -> holdout {best[3]-base_te:+.4f}")

    # nested R=20
    deltas = []
    tops = {a: ranktop((1 - a) * hand_n + a * neigh_mean) for a in alphas}
    for sd in range(20):
        tr, te = {}, {}
        for c, v in full.tiers.items():
            (te if int(hashlib.md5((c + "|" + str(sd)).encode()).hexdigest(), 16) % 2 else tr)[c] = v
        TR = LabelSet("tr", tr, {c: full.gains[c] for c in tr})
        TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        ba = max(alphas, key=lambda a: comp(tops[a], TR))
        deltas.append(comp(tops[ba], TE) - comp(base_ids, TE))
    d = np.array(deltas)
    print(f"\nnested R=20: mean {d.mean():+.4f} std {d.std():.4f} pos {int((d>0).sum())}/20")

    # proxy-inflation diagnostic on the strongest-alpha ranking
    rec_by = {r["cid"]: r for r in recs}
    for a in (0.2, 0.5):
        top = tops[a]
        exp = sum(1 for c in top if rec_by[c].get("cand") and is_anachronistic(rec_by[c]["cand"]))
        print(f"alpha={a}: anachronism exposure {exp}/100  composite(full)={comp(top, full):.4f}")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
