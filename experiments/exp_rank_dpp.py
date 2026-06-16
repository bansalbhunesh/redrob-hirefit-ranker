"""DPP (Determinantal Point Process) reranking — a different mechanism than consensus.

Every rank-aggregation method (RRF/Borda/MC4/Copeland) improves the tail by CONSENSUS, and
all converge at ~0.878 by promoting the anachronism class. DPP improves the tail by
QUALITY x DIVERSITY instead: it selects a subset whose kernel determinant is large, balancing
per-item relevance against pairwise redundancy. If the labels reward covering distinct candidate
types in the 11-50 band (rather than 50 near-duplicates of the same profile), DPP gains through a
channel consensus cannot reach — and it does NOT inherently favour the anachronism class.

Kernel: L = diag(q^theta) . S . diag(q^theta), q = min-max hand score, S = cosine similarity of
the 33-feature vectors (PSD: S = Xn Xn^T). Selection: fast greedy MAP (Chen, Zhang, Zhou,
NeurIPS 2018) with incremental Cholesky — the greedy order IS the ranking. theta trades
relevance (large) vs diversity (small); chosen on TRAIN, reported on untouched holdout + nested.
Golden untouched.
"""
import hashlib
import sys
from collections import Counter

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from _lib import labels, load_pool  # noqa: E402
from exp_rankfusion import comp  # noqa: E402
from redrob_ranker.eval_harness import LabelSet  # noqa: E402

FEATS = None  # set in main from the 33 feature keys


def _feature_matrix(recs):
    keys = sorted(recs[0]["values"].keys())
    X = np.array([[r["values"].get(k, 0.0) for k in keys] for r in recs], dtype=float)
    X -= X.mean(0)
    sd = X.std(0); sd[sd == 0] = 1.0
    X /= sd
    n = np.linalg.norm(X, axis=1, keepdims=True); n[n == 0] = 1.0
    return X / n                       # unit rows -> S = Xn Xn^T is cosine, PSD


def dpp_greedy_order(q, S, k=100, eps=1e-10):
    """Fast greedy MAP for L = diag(q) S diag(q). Returns selection order (best->worst)."""
    N = len(q)
    di2 = (q ** 2).copy()              # diagonal of L = q_i^2 (S_ii=1)
    cis = np.zeros((k, N))
    selected = []
    mask = np.ones(N, dtype=bool)
    for it in range(k):
        di2_masked = np.where(mask, di2, -np.inf)
        j = int(np.argmax(di2_masked))
        if di2[j] <= eps:
            break
        Lj = q[j] * q * S[j]           # L[j, :] = q_j q_i S_ji
        ei = (Lj - cis[:it, j] @ cis[:it, :]) / np.sqrt(di2[j])
        cis[it, :] = ei
        di2 = di2 - ei ** 2
        mask[j] = False
        selected.append(j)
    return selected


def gate_and_nested(recs, base_ids, configs, R=20):
    full, train, test = labels()
    base_te = comp(base_ids, test)
    print(f"baseline: full={comp(base_ids, full):.4f} test={base_te:.4f}\n")
    print(f'{"config":<26}{"full":>9}{"train":>9}{"test":>9}{"t-base":>9}')
    rows, tops = [], {}
    for name, ids in configs:
        tops[name] = ids
        f, tr, te = comp(ids, full), comp(ids, train), comp(ids, test)
        rows.append((name, f)); print(f"{name:<26}{f:>9.4f}{tr:>9.4f}{te:>9.4f}{te - base_te:>+9.4f}")
    deltas, picks = [], []
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
    print(f"\nbest full composite: {max(r[1] for r in rows):.4f}")


def main():
    recs, base_ids = load_pool()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    qn = (hand - hand.min()) / (hand.max() - hand.min() + 1e-12)
    Xn = _feature_matrix(recs)
    print("similarity gram ...")
    S = Xn @ Xn.T
    S = np.clip(S, 0, None)            # keep PSD-ish, non-negative similarity
    # top-lock: keep hand top-L, DPP-select the rest of the 100 from the remaining pool.
    hand_order = sorted(range(len(cids)), key=lambda i: (-hand[i], cids[i]))
    configs = []
    for theta in (1.0, 2.0, 4.0, 8.0):
        for lock in (10, 20, 30):
            q = qn ** theta
            locked = hand_order[:lock]
            lockset = set(locked)
            rest_idx = np.array([i for i in range(len(cids)) if i not in lockset])
            sub_order = dpp_greedy_order(q[rest_idx], S[np.ix_(rest_idx, rest_idx)], k=100 - lock)
            picked = [cids[locked[i]] for i in range(lock)] + [cids[rest_idx[j]] for j in sub_order]
            configs.append((f"DPP th={theta} lock{lock}", picked[:100]))
    print("=" * 66)
    print("DPP RERANK GATE + NESTED")
    print("=" * 66)
    gate_and_nested(recs, base_ids, configs)


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
