"""Build + validate the integrity-constrained submission (NON-golden path). Confirms
the official-validator gate and the integrity gate (0 hard in top-100/top-10). Golden
submission.csv untouched. Score column is rank-monotonic (challenge scores by order)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")

from _lib import load_pool  # noqa: E402
from exp_constrained_fusion import constrained_top100  # noqa: E402
from integrity2 import classify  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402
from redrob_ranker.io import write_submission  # noqa: E402
from redrob_ranker.pipeline import RankerConfig, run_ranking  # noqa: E402
from redrob_ranker.reasoning import build_reason  # noqa: E402
from redrob_ranker.validation import validate_rows  # noqa: E402

OUT = Path("experiments/constrained_submission.csv")


def main():
    recs, base_ids = load_pool()
    ids, hard = constrained_top100(recs)
    assert len(ids) == 100
    in_top100 = sum(1 for c in ids if c in hard)
    in_top10 = sum(1 for c in ids[:10] if c in hard)

    with tempfile.TemporaryDirectory() as tmp:
        res = run_ranking(Path("candidates.jsonl"), Path(tmp) / "o.csv",
                          RankerConfig(top_k=100, candidate_pool_size=0,
                                       max_candidates=None, bm25_backend="auto"))
    feat_by = {c["candidate_id"]: (c, f) for c, f, _ in (res.raw_ranked or [])}

    rows, used, n = [], set(), 100
    for rank, cid in enumerate(ids, 1):
        cand, feat = feat_by[cid]
        rows.append({"candidate_id": cid, "rank": rank,
                     "score": f"{(n - rank + 1) / (n + 1):.6f}",
                     "reasoning": build_reason(cand, feat, rank, used_quotes=used)})
    errors = validate_rows(rows, expected=100)
    print(f"official validator: {'PASS' if not errors else 'FAIL'}")
    for e in errors:
        print("  ", e)
    if errors:
        return
    write_submission(OUT, rows)
    full = load_labels(Path("artifacts/h2_availblind_labels.jsonl"))
    print(f"GATE hard-integrity in top-100: {in_top100}   in top-10: {in_top10}   (require 0/0)")
    print(f"composite (blind): constrained {evaluate(ids, full).composite:.4f}  vs golden "
          f"{evaluate(base_ids, full).composite:.4f}")
    print(f"wrote {OUT} (golden untouched)")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
