"""Expanded-ensemble rank aggregation. Copeland/MC4 over the same 6 families saturate at
~0.8779. This adds 6 MORE orthogonal base rankers (12 total) drawn from the 33-feature set —
education, trust, jd-coverage, scale, seniority, behaviour — so the pairwise-preference graph
carries information the original 6 didn't. Then re-aggregate with Copeland and MC4.

If a richer graph beats 0.8779 the ensemble was the bottleneck; if not, the aggregator was
already extracting all the rank signal the labels contain. Same train-select/nested discipline;
golden untouched.
"""
import hashlib
import sys
from collections import Counter

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from _lib import labels, load_pool  # noqa: E402
from exp_rankfusion import comp, fuse_topk  # noqa: E402
from redrob_ranker.eval_harness import LabelSet  # noqa: E402

V = lambda r, k: r["values"].get(k, 0.0)  # noqa: E731

EXP_FAMILIES = {
    "hand": lambda r: r["hand"],
    "skill": lambda r: V(r, "core_skill_match") + 0.4 * V(r, "skill_depth_score"),
    "aidepth": lambda r: V(r, "ml_ai_tenure_score") + r.get("ai_depth", 0.0),
    "production": lambda r: r.get("production_evidence", 0.0) + V(r, "scale_signal"),
    "lexical": lambda r: V(r, "bm25_score") + V(r, "hyre_similarity"),
    "trajectory": lambda r: V(r, "career_trajectory_score") + V(r, "ir_ranking_experience"),
    # --- new orthogonal families ---
    "education": lambda r: V(r, "education_score") + V(r, "profile_quality"),
    "trust": lambda r: V(r, "endorsement_trust") + V(r, "assessment_score_avg") + V(r, "github_signal"),
    "coverage": lambda r: V(r, "jd_keyword_coverage_score") + V(r, "nice_skill_match") + V(r, "title_match_score"),
    "scale": lambda r: V(r, "scale_signal") + V(r, "product_company_ratio") + V(r, "open_source_signal"),
    "seniority": lambda r: V(r, "senior_title_held") + V(r, "yoe_fit_score") + V(r, "backend_depth_score"),
    "behavior": lambda r: r.get("behavior", 0.0) + V(r, "engagement_score") + V(r, "responsiveness_score"),
}


def rankings_for(recs, fams):
    out = {}
    for fam in fams:
        fn = EXP_FAMILIES[fam]
        scored = sorted(((fn(r), r["cid"]) for r in recs), key=lambda t: (-t[0], t[1]))
        out[fam] = {cid: i + 1 for i, (_, cid) in enumerate(scored)}
    return out


def _beats(cids, ranks, fams):
    N = len(cids)
    ra = {f: np.array([ranks[f][c] for c in cids], dtype=float) for f in fams}
    beats = np.zeros((N, N), dtype=np.int16)
    for f in fams:
        r = ra[f]
        beats += (r[None, :] < r[:, None]).astype(np.int16)
    return beats


def copeland(cids, ranks, fams):
    beats = _beats(cids, ranks, fams)
    thr = len(fams) // 2 + 1
    maj = beats >= thr
    return (maj.sum(axis=0) - maj.sum(axis=1)).astype(float)


def mc4(cids, ranks, fams, iters=400):
    N = len(cids)
    beats = _beats(cids, ranks, fams)
    thr = len(fams) // 2 + 1
    P = (beats >= thr).astype(np.float64) / N
    np.fill_diagonal(P, 0.0)
    P[np.arange(N), np.arange(N)] = 1.0 - P.sum(axis=1)
    pi = np.full(N, 1.0 / N)
    for _ in range(iters):
        nxt = pi @ P
        if np.abs(nxt - pi).sum() < 1e-12:
            return nxt
        pi = nxt
    return pi


def gate_and_nested(recs, base_ids, configs, R=20):
    full, train, test = labels()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    base_te = comp(base_ids, test)
    print(f"baseline: full={comp(base_ids, full):.4f} test={base_te:.4f}\n")
    print(f'{"config":<34}{"full":>9}{"train":>9}{"test":>9}{"t-base":>9}')
    rows, tops = [], {}
    for name, fused, lock in configs:
        top = fuse_topk(recs, fused, hand, lock); tops[name] = top
        f, tr, te = comp(top, full), comp(top, train), comp(top, test)
        rows.append((name, f)); print(f"{name:<34}{f:>9.4f}{tr:>9.4f}{te:>9.4f}{te - base_te:>+9.4f}")
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
    fams = list(EXP_FAMILIES)
    print(f"expanded ensemble: {len(fams)} families")
    ranks = rankings_for(recs, fams)
    cids = [r["cid"] for r in recs]
    cope = copeland(cids, ranks, fams)
    m = mc4(cids, ranks, fams)
    configs = []
    for lock in (0, 20, 30, 40):
        configs.append((f"Copeland12 lock{lock}", cope, lock))
        configs.append((f"MC4-12 lock{lock}", m, lock))
    print("=" * 70)
    print("EXPANDED-ENSEMBLE (12 families) GATE + NESTED")
    print("=" * 70)
    gate_and_nested(recs, base_ids, configs)


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
