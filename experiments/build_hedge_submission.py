"""Full-proof HEDGE submission: severity-gated Copeland (sev<=1.2).

Promote only defensible anachronism candidates (claimed tenure <=1.2x the technology's age,
plausibly rounding); exclude the egregious cases a human would flag. Keeps near-full Copeland
upside while cutting the anachronism-penalty downside below even golden. Non-golden path;
production rank.py untouched. Mirrors build_copeland_submission.py.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool  # noqa: E402
from exp_rankfusion import FAMILIES, rankings  # noqa: E402
from exp_rank_condorcet import copeland_scores  # noqa: E402
from anachronism import is_anachronistic, worst_severity  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402
from redrob_ranker.io import write_submission  # noqa: E402
from redrob_ranker.pipeline import RankerConfig, run_ranking  # noqa: E402
from redrob_ranker.reasoning import build_reason  # noqa: E402
from redrob_ranker.validation import validate_rows  # noqa: E402

OUT = Path("experiments/hedge_submission.csv")
# Optional extra label sets for the post-build comparison print only (does NOT affect the
# produced submission). Defaults to the repo's artifacts/; override with REDROB_LAB_ARTIFACTS.
# Missing files are skipped gracefully, so reproduction never depends on this path.
LAB = Path(os.environ.get("REDROB_LAB_ARTIFACTS", "artifacts"))
SEV_CAP = 1.2


def main():
    recs, base_ids = load_pool()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    by = {r["cid"]: r for r in recs}
    cope = copeland_scores(cids, rankings(recs), list(FAMILIES))
    anach = {c: is_anachronistic(by[c]["cand"]) for c in cids}
    sev = {c: worst_severity(by[c]["cand"]) for c in cids}

    order = sorted(range(len(cids)), key=lambda i: (-hand[i], cids[i]))
    locked = [cids[i] for i in order[:30]]; ls = set(locked)
    rest = [i for i in range(len(cids))
            if cids[i] not in ls and not (anach[cids[i]] and sev[cids[i]] > SEV_CAP)]
    rest.sort(key=lambda i: (-cope[i], cids[i]))
    hedge_ids = (locked + [cids[i] for i in rest])[:100]
    assert len(hedge_ids) == 100

    with tempfile.TemporaryDirectory() as tmp:
        res = run_ranking(Path("candidates.jsonl"), Path(tmp) / "o.csv",
                          RankerConfig(top_k=100, candidate_pool_size=0, max_candidates=None, bm25_backend="auto"))
    feat_by = {c["candidate_id"]: (c, f) for c, f, _ in (res.raw_ranked or [])}
    rows, used = [], set()
    n = len(hedge_ids)
    for rank, cid in enumerate(hedge_ids, start=1):
        cand, feat = feat_by[cid]
        rows.append({"candidate_id": cid, "rank": rank,
                     "score": f"{(n - rank + 1) / (n + 1):.6f}",
                     "reasoning": build_reason(cand, feat, rank, used_quotes=used)})
    errors = validate_rows(rows, expected=100)
    if errors:
        print("VALIDATION FAILED:", errors); return
    write_submission(OUT, rows)
    print(f"wrote {OUT} (golden untouched); anachronism in top100 = {sum(anach[c] for c in hedge_ids)}")

    def c(ids, ls_): return evaluate(ids, ls_).composite
    sets = ["h2_availblind_labels", "merged_j1", "merged_j2", "merged_j3", "relabel_j4", "relabel_g25", "blind_test_frozen"]
    print(f"\n{'label set':<22}{'golden':>9}{'hedge':>9}{'delta':>9}")
    wins = 0
    for nm in sets:
        p = LAB / f"{nm}.jsonl"
        if not p.exists(): continue
        lsr = load_labels(p); g, h = c(base_ids, lsr), c(hedge_ids, lsr)
        wins += h > g + 1e-9
        print(f"{nm:<22}{g:>9.4f}{h:>9.4f}{h - g:>+9.4f}")
    print(f"\nhedge > golden on {wins}/7 label sets")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
