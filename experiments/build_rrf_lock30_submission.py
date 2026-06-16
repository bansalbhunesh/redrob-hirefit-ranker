"""Deterministic builder for the rrf-lock30 candidate submission + the hedge it is compared against,
and the rank-paired set of candidates that DIFFER between them (for the decisive integrity eval).

Writes:
  experiments/rrf_lock30_submission.csv   (gitignored; the candidate ranking)
  experiments/diff_rrf_vs_hedge.json      (gitignored; rank-paired diffs + union for judging)
Production rank.py untouched; both rankings are deterministic post-hoc rerankings of the pool.
"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, "src"); sys.path.insert(0, "experiments")
import numpy as np
from _lib import load_pool
from exp_rankfusion import FAMILIES, rankings, rrf_scores
from exp_rank_condorcet import copeland_scores
from anachronism import is_anachronistic, worst_severity
from redrob_ranker.io import write_submission
from redrob_ranker.pipeline import RankerConfig, run_ranking
from redrob_ranker.reasoning import build_reason
from redrob_ranker.validation import validate_rows

OUT = Path("experiments/rrf_lock30_submission.csv")
DIFF = Path("experiments/diff_rrf_vs_hedge.json")
LOCK, SEV_CAP, RRF_K = 30, 1.2, 60


def main():
    recs, golden = load_pool()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], float)
    by = {r["cid"]: r for r in recs}
    anach = {c: is_anachronistic(by[c]["cand"]) for c in cids}
    sev = {c: worst_severity(by[c]["cand"]) for c in cids}
    rk = rankings(recs); fams = list(FAMILIES)
    cope = copeland_scores(cids, rk, fams)
    rrf = rrf_scores(cids, rk, fams, {f: 1.0 for f in fams}, RRF_K)

    order0 = sorted(range(len(cids)), key=lambda i: (-hand[i], cids[i]))
    locked = [cids[i] for i in order0[:LOCK]]; ls = set(locked)

    # hedge tail: Copeland, drop anachronism sev>1.2
    h_rest = [i for i in range(len(cids)) if cids[i] not in ls and not (anach[cids[i]] and sev[cids[i]] > SEV_CAP)]
    h_rest.sort(key=lambda i: (-cope[i], cids[i]))
    hedge_ids = (locked + [cids[i] for i in h_rest])[:100]

    # rrf-lock30 tail: RRF, no anachronism cap (cap inf)
    r_rest = [i for i in range(len(cids)) if cids[i] not in ls]
    r_rest.sort(key=lambda i: (-rrf[i], cids[i]))
    rrf_ids = (locked + [cids[i] for i in r_rest])[:100]
    assert len(hedge_ids) == 100 and len(rrf_ids) == 100

    # write the rrf submission with grounded reasoning (reuse production feature build)
    with tempfile.TemporaryDirectory() as tmp:
        res = run_ranking(Path("candidates.jsonl"), Path(tmp) / "o.csv",
                          RankerConfig(top_k=100, candidate_pool_size=0, max_candidates=None, bm25_backend="auto"))
    feat = {c["candidate_id"]: (c, f) for c, f, _ in (res.raw_ranked or [])}
    rows, used, n = [], set(), 100
    for rank, cid in enumerate(rrf_ids, 1):
        c, f = feat[cid]
        rows.append({"candidate_id": cid, "rank": rank, "score": f"{(n - rank + 1)/(n + 1):.6f}",
                     "reasoning": build_reason(c, f, rank, used_quotes=used)})
    errs = validate_rows(rows, expected=100)
    if errs:
        print("VALIDATION FAILED:", errs); return
    write_submission(OUT, rows)

    # rank-paired diffs: at each rank, if the two rankings disagree, that's a pair
    pairs = []
    for rank in range(1, 101):
        rc, hc = rrf_ids[rank - 1], hedge_ids[rank - 1]
        if rc != hc:
            pairs.append({"rank": rank, "rrf": rc, "hedge": hc})
    rrf_only = [c for c in rrf_ids if c not in set(hedge_ids)]
    hedge_only = [c for c in hedge_ids if c not in set(rrf_ids)]
    union = sorted(set(rrf_only) | set(hedge_only))
    DIFF.write_text(json.dumps({
        "rrf_ids": rrf_ids, "hedge_ids": hedge_ids, "pairs": pairs,
        "rrf_only": rrf_only, "hedge_only": hedge_only, "union_to_judge": union,
        "anach": {c: bool(anach[c]) for c in union},
        "sev": {c: round(float(sev[c]), 3) for c in union},
    }, indent=0))
    print(f"wrote {OUT} (rrf-lock30). golden untouched.")
    print(f"differing ranks: {len(pairs)} | rrf-only: {len(rrf_only)} | hedge-only: {len(hedge_only)} | union to judge: {len(union)}")
    print(f"anachronism in top100: rrf={sum(anach[c] for c in rrf_ids)} hedge={sum(anach[c] for c in hedge_ids)}")


if __name__ == "__main__":
    import multiprocessing as mp; mp.freeze_support(); main()
