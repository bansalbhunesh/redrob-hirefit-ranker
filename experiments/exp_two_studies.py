"""Golden vs Hedge under ONE identical frozen evaluation protocol.

Study 1  - golden (the pre-registered default), evaluated across the blind arbiter + 6 judge sets.
Study 2  - the SHIPPED hedge, same harness, same sets. RETROSPECTIVE: the Copeland-tail family was
           chosen with these scores visible, so this measures whether the gain is consistent, not
           whether it is out-of-sample.
Study 3  - HOLDOUT: select the hedge's severity threshold on a TRAIN half of the blind arbiter,
           score golden-vs-hedge on the UNTOUCHED test half (single md5%2 split + R repeated 50/50
           splits). Both rankings are fixed before test labels are seen and the construction is
           label-free except the threshold, so this is a clean out-of-sample test of the tail
           reorder -- within the proxy labels (it cannot cleanse the original family choice, and
           none of these are the official hidden labels).

Read-only: submission.csv / golden are never written. Mirrors build_hedge_submission.py exactly.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool  # noqa: E402
from exp_rankfusion import FAMILIES, rankings  # noqa: E402
from exp_rank_condorcet import copeland_scores  # noqa: E402
from anachronism import is_anachronistic, worst_severity  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels, LabelSet  # noqa: E402

LAB = Path("C:/Users/bhune/india-runs-compare-lab/artifacts")
ARBITER = Path("artifacts/h2_availblind_labels.jsonl")
SETS = ["h2_availblind_labels", "merged_j1", "merged_j2", "merged_j3",
        "relabel_j4", "relabel_g25", "blind_test_frozen"]
GRID = [1.0, 1.1, 1.2, 1.3, 1.5, 1e9]   # sev-cap grid; 1e9 = full Copeland tail, 1.0 = clean
SHIPPED_CAP = 1.2


def hedge_order(cids, hand, cope, anach, sev, cap):
    """EXACT shipped construction: lock hand top-30, fill 31-100 by Copeland, drop anachronism
    candidates with severity > cap from the tail."""
    order = sorted(range(len(cids)), key=lambda i: (-hand[i], cids[i]))
    locked = [cids[i] for i in order[:30]]
    ls = set(locked)
    rest = [i for i in range(len(cids))
            if cids[i] not in ls and not (anach[cids[i]] and sev[cids[i]] > cap)]
    rest.sort(key=lambda i: (-cope[i], cids[i]))
    return (locked + [cids[i] for i in rest])[:100]


def split(tiers, gains, salt):
    tr_t, te_t = {}, {}
    for c, v in tiers.items():
        if int(hashlib.md5((c + "|" + str(salt)).encode()).hexdigest(), 16) % 2 == 0:
            tr_t[c] = v
        else:
            te_t[c] = v
    TR = LabelSet("tr", tr_t, {c: gains[c] for c in tr_t})
    TE = LabelSet("te", te_t, {c: gains[c] for c in te_t})
    return TR, TE


def main():
    recs, golden_ids = load_pool()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    by = {r["cid"]: r for r in recs}
    cope = copeland_scores(cids, rankings(recs), list(FAMILIES))
    anach = {c: is_anachronistic(by[c]["cand"]) for c in cids}
    sev = {c: worst_severity(by[c]["cand"]) for c in cids}
    hedge_ids = hedge_order(cids, hand, cope, anach, sev, SHIPPED_CAP)

    a_anach = sum(anach[c] for c in golden_ids[:100])
    h_anach = sum(anach[c] for c in hedge_ids)
    first_div = next((i + 1 for i, (x, y) in enumerate(zip(hedge_ids, golden_ids)) if x != y), None)
    print("MECHANISM (verified):")
    print(f"  hedge = golden top-30 (hand) + Copeland tail (sev<={SHIPPED_CAP}); first divergence rank {first_div}")
    print(f"  anachronism in top-100: golden={a_anach}  hedge={h_anach}")

    # ---- Study 1 + 2: same protocol, full sets, all sub-metrics -------------------------------
    print("\n=== STUDY 1 (golden, pre-registered default)  vs  STUDY 2 (hedge, RETROSPECTIVE) ===")
    print(f"{'label set':<20}{'metric':>8}{'golden':>9}{'hedge':>9}{'delta':>9}")
    wins = 0
    for nm in SETS:
        p = LAB / f"{nm}.jsonl"
        if not p.exists():
            print(f"{nm:<20}  (missing)")
            continue
        L = load_labels(p)
        g, h = evaluate(golden_ids, L), evaluate(hedge_ids, L)
        wins += h.composite > g.composite + 1e-9
        for m in ("composite", "ndcg10", "ndcg50", "map", "p10"):
            gv, hv = getattr(g, m), getattr(h, m)
            tag = nm if m == "composite" else ""
            print(f"{tag:<20}{m:>8}{gv:>9.4f}{hv:>9.4f}{hv - gv:>+9.4f}")
        print()
    print(f"hedge > golden on {wins}/{sum(1 for nm in SETS if (LAB / f'{nm}.jsonl').exists())} label sets (full-set, retrospective)")

    # ---- Study 3: holdout on the blind arbiter ------------------------------------------------
    print("\n=== STUDY 3 (HOLDOUT on the blind arbiter) ===")
    full = load_labels(ARBITER)
    # single md5%2 split (matches _lib.labels())
    TR, TE = split(full.tiers, full.gains, salt="")
    # select threshold on TRAIN
    best_cap, best_tr = None, -1.0
    for cap in GRID:
        hid = hedge_order(cids, hand, cope, anach, sev, cap)
        c = evaluate(hid, TR).composite
        if c > best_tr:
            best_tr, best_cap = c, cap
    hid_star = hedge_order(cids, hand, cope, anach, sev, best_cap)
    g_te = evaluate(golden_ids, TE).composite
    h_te = evaluate(hid_star, TE).composite
    print(f"single split: threshold selected on TRAIN = sev<={best_cap}")
    print(f"  TEST half:  golden={g_te:.4f}  hedge={h_te:.4f}  delta={h_te - g_te:+.4f}"
          f"  [{'GENERALIZES' if h_te > g_te + 1e-4 else 'no out-of-sample gain'}]")

    # R repeated 50/50 splits: select threshold on each train half, score on its test half
    R = 20
    deltas, caps = [], []
    for s in range(R):
        TRr, TEr = split(full.tiers, full.gains, salt=s)
        bc, bt = None, -1.0
        for cap in GRID:
            hid = hedge_order(cids, hand, cope, anach, sev, cap)
            c = evaluate(hid, TRr).composite
            if c > bt:
                bt, bc = c, cap
        hid_s = hedge_order(cids, hand, cope, anach, sev, bc)
        deltas.append(evaluate(hid_s, TEr).composite - evaluate(golden_ids, TEr).composite)
        caps.append(bc)
    arr = np.array(deltas)
    pos = int((arr > 0).sum())
    print(f"R={R} repeated 50/50 splits (threshold reselected on each train half):")
    print(f"  test delta (hedge-golden):  mean {arr.mean():+.4f}  std {arr.std():.4f}"
          f"  pos {pos}/{R}  min {arr.min():+.4f}  max {arr.max():+.4f}")
    from collections import Counter
    print(f"  thresholds chosen across splits: {dict(Counter(caps))}")


if __name__ == "__main__":
    main()
