"""Build a complete, validated ALTERNATIVE submission from the Copeland aggregation
(Condorcet pairwise-win score over the 6 ranker families, top-lock 30 to protect NDCG@10).
Written to a NON-golden path (experiments/copeland_submission.csv); golden is never touched.

Copeland lock30 is the highest-composite validated artifact measured to date (full 0.8779,
nested R=20 +0.0142 / 19-of-20). Like fusion-raw it is the (B) bet — its gain is entirely
NDCG@50 from promoting the anachronism-flagged class (65/100 vs golden's 52). Same score-column
convention as the fusion builder (rank-monotone in (0,1); the metric scores by id ORDER).
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")

import numpy as np  # noqa: E402

from _lib import load_pool  # noqa: E402
from exp_rankfusion import fuse_topk, rankings as build_rankings  # noqa: E402
from exp_rank_condorcet import copeland_scores  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402
from redrob_ranker.io import write_submission  # noqa: E402
from redrob_ranker.pipeline import RankerConfig, run_ranking  # noqa: E402
from redrob_ranker.reasoning import build_reason  # noqa: E402
from redrob_ranker.validation import validate_rows  # noqa: E402

OUT = Path("experiments/copeland_submission.csv")
LAB = Path("C:/Users/bhune/india-runs-compare-lab/artifacts")


def main():
    recs, base_ids = load_pool()
    ranks = build_rankings(recs)
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    cope = copeland_scores(cids, ranks, list(__import__("exp_rankfusion").FAMILIES))
    copeland_ids = fuse_topk(recs, cope, hand, 30)
    assert len(copeland_ids) == 100

    with tempfile.TemporaryDirectory() as tmp:
        res = run_ranking(Path("candidates.jsonl"), Path(tmp) / "o.csv",
                          RankerConfig(top_k=100, candidate_pool_size=0,
                                       max_candidates=None, bm25_backend="auto"))
    feat_by = {c["candidate_id"]: (c, f) for c, f, _ in (res.raw_ranked or [])}

    rows, used = [], set()
    n = len(copeland_ids)
    for rank, cid in enumerate(copeland_ids, start=1):
        cand, feat = feat_by[cid]
        rows.append({
            "candidate_id": cid,
            "rank": rank,
            "score": f"{(n - rank + 1) / (n + 1):.6f}",
            "reasoning": build_reason(cand, feat, rank, used_quotes=used),
        })

    errors = validate_rows(rows, expected=100)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print("  ", e)
        return
    write_submission(OUT, rows)
    print(f"wrote {OUT}  (golden submission.csv untouched)")

    def comp(ids, ls):
        return evaluate(ids, ls).composite
    sets = ["h2_availblind_labels", "merged_j1", "merged_j2", "merged_j3",
            "relabel_j4", "relabel_g25", "blind_test_frozen"]
    print(f"\n{'label set':<22}{'golden':>10}{'copeland':>12}{'delta':>10}")
    wins = 0
    for name in sets:
        p = LAB / f"{name}.jsonl"
        if not p.exists():
            continue
        ls = load_labels(p)
        g, cp = comp(base_ids, ls), comp(copeland_ids, ls)
        wins += cp > g + 1e-9
        print(f"{name:<22}{g:>10.4f}{cp:>12.4f}{cp - g:>+10.4f}")
    print(f"\ncopeland > golden on {wins} label sets (validated alternative submission).")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
