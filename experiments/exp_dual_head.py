"""Dual-head integrity test (Direction 8, P0 centerpiece).

Separate QUALITY (job fit) from INTEGRITY (temporal consistency) and use a GRADED
integrity multiplier instead of the shipped hard 0.0 / soft 0.05. Claim under test:
grading recovers signal the hard penalty discards, for +0.010-0.020 composite.

We reconstruct quality = final_score / honeypot_multiplier (restores the shipped
honeypot penalty so it can be re-applied as a graded head; disqualifier/behavioral stay
in quality -- they are FIT, not integrity). Then:
    dual_head = quality * integrity_grade
    integrity_grade = 0.0           if hard-impossible (shipped honeypot_mult==0)
                    = g_anach        if tech-anachronism (shipped scorer does NOT flag it)
                    = g_amb          if softened class (shipped honeypot_mult==0.05)
                    = 1.0            clean
Rerank all 100K by dual_head; top-100; score on the blind arbiter + nested R=20.

Sweep g_anach and g_amb. g_anach=1.0, g_amb=0.05 must reproduce golden (sanity).
"""
import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from anachronism import is_anachronistic  # noqa: E402
from redrob_ranker.eval_harness import LabelSet, evaluate, load_labels  # noqa: E402
from redrob_ranker.pipeline import RankerConfig, run_ranking  # noqa: E402


def main():
    full = load_labels(Path("artifacts/h2_availblind_labels.jsonl"))
    base = load_labels  # noqa
    with tempfile.TemporaryDirectory() as tmp:
        res = run_ranking(Path("candidates.jsonl"), Path(tmp) / "o.csv",
                          RankerConfig(top_k=100, candidate_pool_size=0,
                                       max_candidates=None, bm25_backend="auto"))
    ranked = res.raw_ranked or []
    golden_ids = [c["candidate_id"] for c in res.rows]
    g0 = evaluate(golden_ids, full).composite

    # reconstruct quality + integrity class per candidate
    rows = []  # (cid, quality, klass)
    for cand, feat, score in ranked:
        hm = feat.honeypot_multiplier
        if hm <= 0.0:
            quality, klass = 0.0, "hard"           # blocked regardless
        else:
            quality = score / hm                    # restore pre-honeypot quality
            if abs(hm - 0.05) < 1e-6:
                klass = "ambiguous"
            else:
                klass = "anachronism" if is_anachronistic(cand) else "clean"
        rows.append((cand["candidate_id"], quality, klass))

    def rerank(g_anach, g_amb):
        grade = {"hard": 0.0, "anachronism": g_anach, "ambiguous": g_amb, "clean": 1.0}
        scored = [(cid, q * grade[k], cid) for cid, q, k in rows]
        scored.sort(key=lambda t: (-t[1], t[2]))
        return [t[0] for t in scored[:100]]

    print(f"golden composite (blind): {g0:.4f}\n")
    print(f"{'g_anach':>8}{'g_amb':>7}{'composite':>11}{'d-golden':>10}  note")
    configs = [(1.0, 0.05, "= golden (sanity)"), (1.0, 0.40, "rescue ambiguous only"),
               (0.5, 0.40, "soft-penalize anachronism"), (0.3, 0.40, "dual-head proposal"),
               (0.0, 0.40, "hard-exclude anachronism"), (1.0, 1.0, "no integrity penalty at all")]
    keep = {}
    for ga, gm, note in configs:
        ids = rerank(ga, gm)
        c = evaluate(ids, full).composite
        keep[(ga, gm)] = ids
        print(f"{ga:>8.2f}{gm:>7.2f}{c:>11.4f}{c - g0:>+10.4f}  {note}")

    # nested R=20 for the dual-head proposal vs golden
    ids = keep[(0.3, 0.40)]
    deltas = []
    for s in range(20):
        te = {c: v for c, v in full.tiers.items()
              if int(hashlib.md5((c + "|" + str(s)).encode()).hexdigest(), 16) % 2}
        TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        deltas.append(evaluate(ids, TE).composite - evaluate(golden_ids, TE).composite)
    d = np.array(deltas)
    print(f"\ndual-head proposal (0.3/0.40) nested R=20 vs golden: mean {d.mean():+.4f} pos {int((d>0).sum())}/20")
    from collections import Counter
    kl = Counter(k for _, _, k in rows)
    print(f"class counts over 100K: {dict(kl)}")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
