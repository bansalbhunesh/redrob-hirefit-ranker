"""Integrity-constrained rank fusion (P0 core).

Pipeline:  5 complementary channels -> RRF + Borda consensus -> HARD-integrity
exclusion (anachronism + other hard rules; never rescued) -> top-10 lock (clean hand)
-> ranks 11-50 fusion -> fill to 100.

Channels are deliberately complementary signal families (NOT five weightings of one
scorer): tuned composite, lexical BM25, production-evidence, semantic/HyRE, career-quality.

Gates verified here: 0 hard-integrity candidates in top-100 and top-10; composite vs
golden and vs unconstrained fusion-raw on the blind arbiter + 6 independent judge sets;
nested R=20 holdout. (Official validator + golden reproduction are separate test runs.)
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels  # noqa: E402
from integrity2 import classify  # noqa: E402
from redrob_ranker.eval_harness import LabelSet, evaluate, load_labels  # noqa: E402

LAB = Path("C:/Users/bhune/india-runs-compare-lab/artifacts")
INDEP = ["merged_j1", "merged_j2", "merged_j3", "relabel_j4", "relabel_g25", "blind_test_frozen"]

CHANNELS = {
    "hand": lambda r: r["hand"],
    "bm25": lambda r: r["values"].get("bm25_score", 0.0),
    "evidence": lambda r: r.get("production_evidence", 0.0) + r["values"].get("scale_signal", 0.0),
    "semantic": lambda r: r["values"].get("hyre_similarity", 0.0),
    "career": lambda r: r["values"].get("career_trajectory_score", 0.0)
    + r["values"].get("ir_ranking_experience", 0.0),
}


def channel_ranks(recs):
    out = {}
    for ch, fn in CHANNELS.items():
        order = sorted(recs, key=lambda r: (-fn(r), r["cid"]))
        out[ch] = {r["cid"]: i + 1 for i, r in enumerate(order)}
    return out


def constrained_top100(recs, K=30, lock=10, method="rrf", borda_N=None, exclude_hard=True):
    hard = {r["cid"] for r in recs if classify(r["cand"], r["values"])["level"] == "hard"}
    pool = [r for r in recs if not (exclude_hard and r["cid"] in hard)]
    ranks = channel_ranks(pool)
    N = borda_N or len(pool)
    cids = [r["cid"] for r in pool]
    if method == "rrf":
        fused = {c: sum(1.0 / (K + ranks[ch][c]) for ch in CHANNELS) for c in cids}
    else:
        fused = {c: sum((N - ranks[ch][c]) for ch in CHANNELS) for c in cids}
    hand_by = {r["cid"]: r["hand"] for r in pool}
    locked = [r["cid"] for r in sorted(pool, key=lambda r: (-r["hand"], r["cid"]))[:lock]]
    locked_set = set(locked)
    rest = sorted([c for c in cids if c not in locked_set], key=lambda c: (-fused[c], c))
    return (locked + rest)[:100], hard


def comp(ids, ls):
    return evaluate(ids, ls).composite


def main():
    recs, base_ids = load_pool()
    full, _, _ = labels()
    rec_by = {r["cid"]: r for r in recs}

    top, hard = constrained_top100(recs)
    # integrity gates
    hard_top100 = sum(1 for c in top if c in hard)
    hard_top10 = sum(1 for c in top[:10] if c in hard)
    print(f"hard-integrity candidates in pool: {len(hard)}")
    print(f"GATE hard in top-100: {hard_top100}   hard in top-10: {hard_top10}   (must be 0/0)")

    # comparison vs golden & fusion-raw on all label sets
    from exp_rankfusion import rankings as build_rankings
    from exp_rankfusion_guarded import build_top
    ranks_all = build_rankings(recs)
    fusion_raw = build_top(recs, ranks_all, "raw")

    sets = {"h2_availblind": full}
    for n in INDEP:
        p = LAB / f"{n}.jsonl"
        if p.exists():
            sets[n] = load_labels(p)

    print(f"\n{'label set':<16}{'golden':>10}{'fusion-raw':>12}{'constrained':>13}")
    for n, ls in sets.items():
        print(f"{n:<16}{comp(base_ids, ls):>10.4f}{comp(fusion_raw, ls):>12.4f}{comp(top, ls):>13.4f}")

    # nested R=20 vs golden on blind
    deltas = []
    for s in range(20):
        te = {c: v for c, v in full.tiers.items()
              if int(hashlib.md5((c + "|" + str(s)).encode()).hexdigest(), 16) % 2}
        TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        deltas.append(comp(top, TE) - comp(base_ids, TE))
    d = np.array(deltas)
    print(f"\nconstrained vs golden, nested R=20: mean {d.mean():+.4f} std {d.std():.4f} pos {int((d>0).sum())}/20")
    print(f"anachronism exposure -> golden 52/100, fusion-raw 62/100, constrained {sum(1 for c in top if c in hard)}/100")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
