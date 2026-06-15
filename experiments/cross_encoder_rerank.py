"""Offline, blind-gated cross-encoder rerank experiment.

Hypothesis (from field evidence): a top-K cross-encoder rerank lifts NDCG@10 — the
50%-weighted metric — where external cross-encoder baselines beat our hand
pipeline (0.829). We replicate a standard recipe (ms-marco-MiniLM-L-6-v2, blend
CE with hand score) on OUR pool and gate every variant on the 100K frozen blind set.

Does NOT touch src/redrob_ranker/ or the golden submission. Reruns the hand pipeline
read-only, reranks the top-500 pool, scores variants. Baseline (w_ce=0) reproduces 0.862.

CAVEAT: w_ce is swept ON the blind arbiter, so the best-on-blind weight is optimistic
(in-sample). Real adoption needs train/holdout gating like our prior measured negatives.

Run: python experiments/cross_encoder_rerank.py   (from repo root)
"""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np

POOL = 500


def minmax(x):
    x = np.asarray(x, dtype=float)
    lo, hi = float(x.min()), float(x.max())
    return (x - lo) / (hi - lo) if hi > lo else np.full_like(x, 0.5)


def main():
    from redrob_ranker.pipeline import RankerConfig, run_ranking
    from redrob_ranker.text import candidate_text
    from redrob_ranker.constants import JD_QUERY
    from redrob_ranker.eval_harness import load_labels, evaluate
    from sentence_transformers import CrossEncoder

    labels = load_labels(Path("artifacts/h2_availblind_labels.jsonl"))
    jd_full = Path("job_description.txt").read_text(encoding="utf-8")[:2000]

    print("running hand pipeline (golden config: top_k=100, pool=0, full 100K)...", flush=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "o.csv"
        res = run_ranking(Path("candidates.jsonl"), out,
                          RankerConfig(top_k=100, candidate_pool_size=0, max_candidates=None, bm25_backend="auto"))
    print(f"  ranked in {time.time()-t0:.0f}s | raw_ranked pool = {len(res.raw_ranked or [])}", flush=True)

    base_ids = [r["candidate_id"] for r in res.rows]
    ev0 = evaluate(base_ids, labels)
    print(f"BASELINE (hand golden):  comp={ev0.composite:.4f}  N@10={ev0.ndcg10:.4f}  N@50={ev0.ndcg50:.4f}\n", flush=True)

    pool = (res.raw_ranked or [])[:POOL]
    cands = [c for c, _, _ in pool]
    hand = np.array([s for _, _, s in pool], dtype=float)
    cids = [c["candidate_id"] for c in cands]
    texts = [candidate_text(c) for c in cands]
    hand_n = minmax(hand)

    best = None
    for jd_name, jd in [("JD_QUERY", JD_QUERY.strip()), ("JD_FULL_2000", jd_full)]:
        ce = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        t = time.time()
        ce_scores = ce.predict([(jd, tx) for tx in texts], show_progress_bar=False)
        ce_n = minmax(ce_scores)
        print(f"--- JD repr: {jd_name}  (CE predict {time.time()-t:.1f}s on {len(texts)} pairs) ---", flush=True)
        print(f'{"w_ce":>6}{"comp":>9}{"N@10":>8}{"N@50":>8}{"vs_base":>9}')
        for w in [0.00, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.70, 1.00]:
            final = (1 - w) * hand_n + w * ce_n
            order = sorted(range(len(cids)), key=lambda i: (-final[i], cids[i]))
            top100 = [cids[i] for i in order[:100]]
            ev = evaluate(top100, labels)
            d = ev.composite - ev0.composite
            flag = "  <-- beats baseline" if d > 1e-9 else ""
            print(f"{w:>6.2f}{ev.composite:>9.4f}{ev.ndcg10:>8.4f}{ev.ndcg50:>8.4f}{d:>+9.4f}{flag}", flush=True)
            if best is None or ev.composite > best[0]:
                best = (ev.composite, ev.ndcg10, ev.ndcg50, w, jd_name)
        print()

    print(f"BEST variant: comp={best[0]:.4f} N@10={best[1]:.4f} N@50={best[2]:.4f} "
          f"at w_ce={best[3]} ({best[4]}) vs baseline {ev0.composite:.4f} (delta {best[0]-ev0.composite:+.4f})")
    print("NOTE: best-on-blind is in-sample/optimistic; adoption requires train/holdout gating.")
    print("DONE")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
