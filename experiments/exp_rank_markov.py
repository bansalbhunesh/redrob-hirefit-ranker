"""Obscure rank-aggregation study — methods the field (and judges) rarely touch.

Prior rank-space work (#13) used Reciprocal Rank Fusion and Borda. Those are POSITIONAL
aggregators: they sum a function of each item's rank. They cannot model transitive
pairwise structure ("A usually beats B, B usually beats C, so lift A") the way a
preference-graph method can. This study tests two such methods, neither tried before here:

  1. MC4 — Markov-chain rank aggregation (Dwork, Kumar, Naor, Sivakumar, WWW 2001).
     Build a random walk over candidates: from c, propose a uniform-random d and move
     there iff a MAJORITY of the 6 rankers rank d above c. The stationary distribution
     of that chain is the consensus order. It is scale-free and captures the pairwise
     majority graph, not just average position.

  2. Plackett–Luce MLE (Hunter, MM algorithms, Ann. Statist. 2004).
     Fit a latent "worth" gamma_i to each candidate from the 6 full rankings via the
     minorize–maximize update; rank by gamma. This is the maximum-likelihood consensus
     under the Luce choice axiom.

DISCIPLINE (identical to #13): train-select every hyperparameter on a TRAIN label half,
report the untouched-holdout delta, then a NESTED R=20 selection test for honest
out-of-sample generalization. The 100K frozen blind set is the arbiter; golden is never
touched. A method that does not beat baseline on the nested test is measured-negative #14.

Run from repo root after experiments/_build_pool.py.
"""
import hashlib
import sys
from collections import Counter

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from _lib import labels, load_pool  # noqa: E402
from exp_rankfusion import FAMILIES, comp, fuse_topk, rankings  # noqa: E402
from redrob_ranker.eval_harness import LabelSet  # noqa: E402


def _rank_arrays(cids, ranks):
    """Per-family 1-indexed rank as float arrays aligned to `cids` order."""
    return {f: np.array([ranks[f][c] for c in cids], dtype=float) for f in FAMILIES}


# ── MC4: stationary distribution of the majority-preference random walk ──────────
def mc4_scores(cids, ranks, fams, maj_threshold=None, iters=400, tol=1e-12):
    N = len(cids)
    ra = _rank_arrays(cids, ranks)
    nf = len(fams)
    thr = maj_threshold if maj_threshold is not None else (nf // 2 + 1)
    # beats[c, d] = # of families that rank d strictly above c  (lower rank = better)
    beats = np.zeros((N, N), dtype=np.int16)
    for f in fams:
        r = ra[f]
        beats += (r[None, :] < r[:, None]).astype(np.int16)
    maj = (beats >= thr).astype(np.float64)          # 1 where a majority prefers d over c
    P = maj / N                                       # uniform proposal, accept on majority
    np.fill_diagonal(P, 0.0)
    P[np.arange(N), np.arange(N)] = 1.0 - P.sum(axis=1)   # self-loop holds the rest
    pi = np.full(N, 1.0 / N)
    for _ in range(iters):
        nxt = pi @ P
        if np.abs(nxt - pi).sum() < tol:
            pi = nxt
            break
        pi = nxt
    return pi                                          # higher stationary mass = better


# ── Plackett–Luce worth via the MM algorithm (full-ranking contests) ─────────────
def plackett_luce_scores(cids, ranks, fams, iters=300, tol=1e-9):
    N = len(cids)
    ra = _rank_arrays(cids, ranks)
    # Each family is one full ranking (a contest). Precompute, per family, the item
    # order (best->worst) so we can use the reverse-cumsum MM update in O(N) per family.
    orders = {f: np.argsort(ra[f], kind="stable") for f in fams}   # indices best->worst
    gamma = np.full(N, 1.0 / N)
    for _ in range(iters):
        denom = np.zeros(N)
        # w_i = number of contests in which i is chosen while still "available" = it is
        # ranked ahead of >=1 remaining item; for a full ranking every item except the
        # last contributes one win. MM denominator accumulates 1/(sum of gamma of the
        # remaining set) at each position the item is still available.
        wins = np.zeros(N)
        for f in fams:
            o = orders[f]
            g = gamma[o]                              # gammas in best->worst order
            # remaining-set gamma sum at each position = reverse cumulative sum
            tail = np.cumsum(g[::-1])[::-1]           # tail[k] = sum gamma[k:]
            inv = 1.0 / np.maximum(tail, 1e-300)
            contrib = np.cumsum(inv)                  # item at position p sees sum_{k<=p} inv[k]
            denom[o] += contrib
            wins[o[:-1]] += 1.0                       # every item but the last wins once
        new = wins / np.maximum(denom, 1e-300)
        new /= new.sum()
        if np.abs(new - gamma).sum() < tol:
            gamma = new
            break
        gamma = new
    return gamma


# ── gate: train-select strength/lock, report untouched-holdout delta ─────────────
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
        rows.append((name, f, tr, te, te - base_te))
        print(f"{name:<40}{f:>9.4f}{tr:>9.4f}{te:>9.4f}{te - base_te:>+9.4f}")
    best = max(rows, key=lambda r: r[2])               # train-best ONLY
    print(f"\ntrain-best: {best[0]}  ->  HOLDOUT delta {best[3] - base_te:+.4f}  "
          f"[{'GENERALIZES' if best[3] - base_te > 1e-4 else 'rejected (in-sample only)'}]")
    return base_f, base_te, rows, tops


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

    print("computing MC4 stationary distribution ...")
    mc4 = mc4_scores(cids, ranks, fams)
    print("computing Plackett-Luce worth ...")
    pl = plackett_luce_scores(cids, ranks, fams)

    # Top-lock protects NDCG@10 (0.50 weight); the tail is where NDCG@50 lives.
    configs = []
    for lock in (0, 10, 20, 30):
        configs.append((f"MC4 lock{lock}", mc4, lock))
        configs.append((f"PlackettLuce lock{lock}", pl, lock))

    print("\n" + "=" * 74)
    print("OBSCURE RANK-AGGREGATION GATE (train-select, holdout-report)")
    print("=" * 74)
    base_f, base_te, rows, tops = gate(recs, base_ids, configs)
    print("\n" + "=" * 74)
    print("NESTED REPEATED HOLDOUT (R=20): honest procedure-generalization test")
    print("=" * 74)
    nested(recs, base_ids, configs, tops, R=20)
    print(f"\nbest full-set composite among obscure fusions: {max(r[1] for r in rows):.4f}  "
          f"(baseline {base_f:.4f})")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
