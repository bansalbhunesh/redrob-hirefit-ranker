"""Rank-space fusion study (novel direction; not covered by measured negatives #1-#12).

WHY THIS IS DIFFERENT
---------------------
All twelve prior measured negatives operate in SCORE space: they blend a new signal
into the linear composite (or replace the model) and re-rank globally. The hand score
is a tuned 22-feature linear sum * guardrail multipliers, so a global score-blend
perturbs the near-perfect top-10 (0.50 weight) to chase NDCG@50 (0.30 weight, the
documented weak spot).

This study asks a structurally different question: holding the feature set fixed,
is a LINEAR score-sum the right aggregator, or does RANK-space consensus order the
11-50 tail better against the hidden labels? Rank fusion (Reciprocal Rank Fusion,
Cormack/Clarke/Buttcher SIGIR 2009; and Borda count) is scale-free -- immune to the
per-feature calibration problems that can dominate a linear sum -- and it admits a
TOP-LOCK: freeze the hand top-L (protect NDCG@10) and re-fuse only the tail. No
score-blend can do that, and the competitor field does not do it.

DISCIPLINE (identical to #11/#12)
- Build the ranking, choose every hyperparameter on a TRAIN label half, report the
  delta on an untouched TEST half. Single-split "wins" are then re-checked with R=20
  repeated 50/50 holdouts; anything that does not stay positive across repeats is
  noise and is rejected.
- The 100K frozen blind set is the arbiter. Golden submission is never touched.

Run from repo root after experiments/_build_pool.py.
"""
import hashlib
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from _lib import load_pool, labels, minmax  # noqa: E402
from redrob_ranker.eval_harness import LabelSet, evaluate  # noqa: E402

# -----------------------------------------------------------------------------
# Ranker families. Each maps a candidate -> a scalar; higher = better. We rank the
# whole 3000-pool by each and fuse the rank positions. Families are chosen to be as
# orthogonal as the (comprehensive) feature set allows: skill match, AI depth,
# production evidence, lexical/semantic similarity, career trajectory.
# -----------------------------------------------------------------------------
FAMILIES = {
    "hand": lambda r: r["hand"],
    "skill": lambda r: r["values"].get("core_skill_match", 0.0)
    + 0.4 * r["values"].get("skill_depth_score", 0.0),
    "aidepth": lambda r: r["values"].get("ml_ai_tenure_score", 0.0)
    + r.get("ai_depth", 0.0),
    "production": lambda r: r.get("production_evidence", 0.0)
    + r["values"].get("scale_signal", 0.0),
    "lexical": lambda r: r["values"].get("bm25_score", 0.0)
    + r["values"].get("hyre_similarity", 0.0),
    "trajectory": lambda r: r["values"].get("career_trajectory_score", 0.0)
    + r["values"].get("ir_ranking_experience", 0.0),
}


def rankings(recs):
    """For each family, return {cid: 1-indexed rank} over the full pool.
    Ties broken by cid for determinism (matches eval_harness ordering)."""
    out = {}
    for fam, fn in FAMILIES.items():
        scored = [(fn(r), r["cid"]) for r in recs]
        scored.sort(key=lambda t: (-t[0], t[1]))
        out[fam] = {cid: i + 1 for i, (_, cid) in enumerate(scored)}
    return out


def rrf_scores(cids, ranks, fams, weights, K):
    """Reciprocal Rank Fusion: score(c) = sum_f w_f / (K + rank_f(c))."""
    return np.array(
        [sum(weights.get(f, 1.0) / (K + ranks[f][c]) for f in fams) for c in cids],
        dtype=float,
    )


def borda_scores(cids, ranks, fams, weights, N):
    """Weighted Borda: score(c) = sum_f w_f * (N - rank_f(c))."""
    return np.array(
        [sum(weights.get(f, 1.0) * (N - ranks[f][c]) for f in fams) for c in cids],
        dtype=float,
    )


def fuse_topk(recs, fused, hand, lock_L, k=100):
    """Final top-k ordering. Lock the hand top-`lock_L`, then fill the remaining
    slots by the fused score (this is what lets consensus promote a candidate the
    hand ranker buried in the tail). lock_L=0 => pure global fusion."""
    cids = [r["cid"] for r in recs]
    hand_order = sorted(range(len(cids)), key=lambda i: (-hand[i], cids[i]))
    locked = [cids[i] for i in hand_order[:lock_L]]
    locked_set = set(locked)
    rest = [i for i in range(len(cids)) if cids[i] not in locked_set]
    rest.sort(key=lambda i: (-fused[i], cids[i]))
    tail = [cids[i] for i in rest]
    return (locked + tail)[:k]


def comp(ids, ls):
    return evaluate(ids, ls).composite


def gate_fusion(recs, base_ids, ranks, configs):
    """Choose the train-best config, report its untouched-holdout delta."""
    full, train, test = labels()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    N = len(cids)
    base_f, base_tr, base_te = comp(base_ids, full), comp(base_ids, train), comp(base_ids, test)
    print(f"baseline: full={base_f:.4f} train={base_tr:.4f} test={base_te:.4f}\n")
    print(f'{"config":<46}{"full":>8}{"train":>8}{"test":>8}{"t-base":>9}')
    rows = []
    for name, fams, weights, method, K, lock in configs:
        if method == "rrf":
            fused = rrf_scores(cids, ranks, fams, weights, K)
        else:
            fused = borda_scores(cids, ranks, fams, weights, N)
        top = fuse_topk(recs, fused, hand, lock)
        f, tr, te = comp(top, full), comp(top, train), comp(top, test)
        rows.append((name, f, tr, te, te - base_te))
        print(f"{name:<46}{f:>8.4f}{tr:>8.4f}{te:>8.4f}{te - base_te:>+9.4f}")
    best = max(rows, key=lambda r: r[2])  # train-best ONLY
    print(f"\ntrain-best: {best[0]}  ->  HOLDOUT delta {best[3] - base_te:+.4f}")
    return base_f, rows


def repeated_holdout(recs, base_ids, ranks, config, R=20):
    """R repeated 50/50 splits; pick nothing per-split (config is fixed) -- just
    measure the test-half delta of this single fixed config across resamples."""
    full, _, _ = labels()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    N = len(cids)
    name, fams, weights, method, K, lock = config
    fused = rrf_scores(cids, ranks, fams, weights, K) if method == "rrf" else borda_scores(cids, ranks, fams, weights, N)
    top = fuse_topk(recs, fused, hand, lock)
    deltas = []
    for s in range(R):
        te = {c: v for c, v in full.tiers.items()
              if int(hashlib.md5((c + "|" + str(s)).encode()).hexdigest(), 16) % 2}
        TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        deltas.append(comp(top, TE) - comp(base_ids, TE))
    a = np.array(deltas)
    print(f"{name:<46} mean {a.mean():+.4f} std {a.std():.4f} pos {int((a>0).sum())}/{R} "
          f"min {a.min():+.4f} max {a.max():+.4f}")
    return a


def nested_repeated(recs, base_ids, ranks, configs, R=20):
    """HONEST generalization test: for each of R 50/50 splits, SELECT the train-best
    config on that split's train half, score it on the untouched test half. This is
    the procedure's true out-of-sample delta (no peeking at full-set), matching the
    discipline of _lib.gate_repeat. Reports which configs the selector keeps picking."""
    full, _, _ = labels()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    N = len(cids)
    # Precompute the top-100 ordering for every config once (splits only change labels).
    tops = {}
    for c in configs:
        name, fams, weights, method, K, lock = c
        fused = rrf_scores(cids, ranks, fams, weights, K) if method == "rrf" else borda_scores(cids, ranks, fams, weights, N)
        tops[name] = fuse_topk(recs, fused, hand, lock)
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
    from collections import Counter
    print(f"nested-select procedure: mean {a.mean():+.4f} std {a.std():.4f} "
          f"pos {int((a>0).sum())}/{R} min {a.min():+.4f} max {a.max():+.4f}")
    print("configs picked by train-selector:")
    for nm, ct in Counter(picks).most_common():
        print(f"  {ct:>2}x  {nm}")
    return a


def main():
    recs, base_ids = load_pool()
    ranks = rankings(recs)
    eq = {f: 1.0 for f in FAMILIES}
    hand_heavy = {**{f: 1.0 for f in FAMILIES}, "hand": 3.0}

    # Coarse grid: method x ranker-set x K x top-lock. Kept modest on purpose;
    # repeated-holdout (below) is the real guard against grid overfitting.
    configs = []
    for K in (10, 30, 60):
        configs.append((f"RRF all eq K={K} lock0", list(FAMILIES), eq, "rrf", K, 0))
        configs.append((f"RRF all handheavy K={K} lock0", list(FAMILIES), hand_heavy, "rrf", K, 0))
        for lock in (10, 20, 30):
            configs.append((f"RRF all eq K={K} lock{lock}", list(FAMILIES), eq, "rrf", K, lock))
            configs.append((f"RRF hand+lexical K={K} lock{lock}", ["hand", "lexical"], eq, "rrf", K, lock))
    configs.append(("Borda all eq lock0", list(FAMILIES), eq, "borda", 0, 0))
    configs.append(("Borda all eq lock20", list(FAMILIES), eq, "borda", 0, 20))
    configs.append(("Borda hand-heavy lock20", list(FAMILIES), hand_heavy, "borda", 0, 20))

    print("=" * 78)
    print("RANK-FUSION GATE (train-select, holdout-report)")
    print("=" * 78)
    base_f, rows = gate_fusion(recs, base_ids, ranks, configs)

    # Repeated-holdout on the configs that even tied baseline on full -- if none
    # clear baseline there is nothing to confirm, but we still stress the top-3.
    top3 = sorted(rows, key=lambda r: -r[3])[:3]
    print("\n" + "=" * 78)
    print("REPEATED HOLDOUT (R=20) on top-3 full-set configs")
    print("=" * 78)
    cfg_by_name = {c[0]: c for c in configs}
    for r in top3:
        repeated_holdout(recs, base_ids, ranks, cfg_by_name[r[0]], R=20)

    print("\n" + "=" * 78)
    print("NESTED REPEATED HOLDOUT (R=20): the honest procedure-generalization test")
    print("=" * 78)
    nested_repeated(recs, base_ids, ranks, configs, R=20)

    print(f"\nbest full-set composite among fusions: {max(r[1] for r in rows):.4f}  "
          f"(baseline {base_f:.4f})")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
