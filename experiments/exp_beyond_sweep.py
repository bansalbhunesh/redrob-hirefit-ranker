"""Beyond-hedge sweep: aggregator x lock-size x severity-cap, blind-arbiter, holdout-gated.
Goal: find a config that beats golden 0.8625 / hedge 0.8748 / full-Copeland 0.8779 — and prove it
generalizes (md5 train/test). Read-only."""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, "src"); sys.path.insert(0, "experiments")
import numpy as np
from _lib import load_pool
from exp_rankfusion import FAMILIES, rankings, rrf_scores, borda_scores
from exp_rank_condorcet import copeland_scores
from exp_rank_markov import mc4_scores, plackett_luce_scores
from anachronism import is_anachronistic, worst_severity
from redrob_ranker.eval_harness import evaluate, load_labels, LabelSet

ARB = Path("artifacts/h2_availblind_labels.jsonl")
LOCKS = [0, 20, 30, 40, 50]
CAPS = [1.0, 1.1, 1.2, 1.3, 1.5, 1e9]


def order(cids, hand, agg, anach, sev, lock, cap):
    o = sorted(range(len(cids)), key=lambda i: (-hand[i], cids[i]))
    locked = [cids[i] for i in o[:lock]]; ls = set(locked)
    rest = [i for i in range(len(cids)) if cids[i] not in ls and not (anach[cids[i]] and sev[cids[i]] > cap)]
    rest.sort(key=lambda i: (-agg[i], cids[i]))
    return (locked + [cids[i] for i in rest])[:100]


def split(t, g, salt):
    tr = {c: v for c, v in t.items() if int(hashlib.md5((c + str(salt)).encode()).hexdigest(), 16) % 2 == 0}
    te = {c: v for c, v in t.items() if c not in tr}
    return LabelSet("tr", tr, {c: g[c] for c in tr}), LabelSet("te", te, {c: g[c] for c in te})


def main():
    recs, golden = load_pool()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], float)
    by = {r["cid"]: r for r in recs}
    anach = {c: is_anachronistic(by[c]["cand"]) for c in cids}
    sev = {c: worst_severity(by[c]["cand"]) for c in cids}
    rk = rankings(recs); fams = list(FAMILIES); w = {f: 1.0 for f in fams}; N = len(cids)
    print("computing aggregator scores ...")
    aggs = {
        "copeland": copeland_scores(cids, rk, fams),
        "borda": borda_scores(cids, rk, fams, w, N),
        "rrf": rrf_scores(cids, rk, fams, w, 60),
        "mc4": mc4_scores(cids, rk, fams),
        "pl": plackett_luce_scores(cids, rk, fams),
    }
    L = load_labels(ARB)
    g_full = evaluate(golden, L).composite
    TR, TE = split(L.tiers, L.gains, "")
    g_te = evaluate(golden, TE).composite
    print(f"baselines: golden full={g_full:.4f} test={g_te:.4f} | hedge 0.8748 | copeland 0.8779\n")
    rows = []
    for name, sc in aggs.items():
        for lock in LOCKS:
            for cap in CAPS:
                ids = order(cids, hand, sc, anach, sev, lock, cap)
                full = evaluate(ids, L).composite
                te = evaluate(ids, TE).composite
                rows.append((full, te, name, lock, cap))
    rows.sort(reverse=True)
    print(f"{'full':>8}{'test':>8}  agg        lock  cap")
    for full, te, name, lock, cap in rows[:12]:
        tag = " <-- beats copeland" if full > 0.8779 + 1e-9 else (" <- beats hedge" if full > 0.8748 + 1e-9 else "")
        print(f"{full:>8.4f}{te:>8.4f}  {name:<9} {lock:>4}  {cap if cap < 9 else 'inf':>4}{tag}")
    best = rows[0]
    print(f"\nbest full = {best[0]:.4f} ({best[2]} lock{best[3]} cap{best[4] if best[4]<9 else 'inf'})  "
          f"vs golden {g_full:.4f}; holdout test delta vs golden = {best[1]-g_te:+.4f}")


if __name__ == "__main__":
    import multiprocessing as mp; mp.freeze_support(); main()
