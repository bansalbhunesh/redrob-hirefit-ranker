"""Train/holdout validation of the cross-encoder rerank.

The sweep in cross_encoder_rerank.py picks w_ce ON the blind arbiter (in-sample,
optimistic). This splits the 100K blind labels by candidate-id hash into TRAIN and
TEST halves, selects w_ce purely on TRAIN, and reports the gain on the untouched
TEST half — the honest, generalization-safe number.

Run: python experiments/cross_encoder_holdout.py   (from repo root)
"""
import hashlib
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np

POOL = 500
SWEEP = [0.00, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.70]


def minmax(x):
    x = np.asarray(x, dtype=float)
    lo, hi = float(x.min()), float(x.max())
    return (x - lo) / (hi - lo) if hi > lo else np.full_like(x, 0.5)


def main():
    from redrob_ranker.pipeline import RankerConfig, run_ranking
    from redrob_ranker.text import candidate_text
    from redrob_ranker.eval_harness import load_labels, evaluate, LabelSet

    full = load_labels(Path("artifacts/h2_availblind_labels.jsonl"))
    jd_full = Path("job_description.txt").read_text(encoding="utf-8")[:2000]

    def bucket(cid):
        return int(hashlib.md5(cid.encode()).hexdigest(), 16) % 2

    tr_t = {c: v for c, v in full.tiers.items() if bucket(c) == 0}
    te_t = {c: v for c, v in full.tiers.items() if bucket(c) == 1}
    TRAIN = LabelSet("train", tr_t, {c: full.gains[c] for c in tr_t})
    TEST = LabelSet("test", te_t, {c: full.gains[c] for c in te_t})
    print(f"split: train labels={len(tr_t)}  test labels={len(te_t)}", flush=True)

    print("running hand pipeline...", flush=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        res = run_ranking(Path("candidates.jsonl"), Path(tmp) / "o.csv",
                          RankerConfig(top_k=100, candidate_pool_size=0, max_candidates=None, bm25_backend="auto"))
    print(f"  ranked in {time.time()-t0:.0f}s", flush=True)

    base_ids = [r["candidate_id"] for r in res.rows]
    base_tr = evaluate(base_ids, TRAIN).composite
    base_te = evaluate(base_ids, TEST).composite

    pool = (res.raw_ranked or [])[:POOL]
    cands = [c for c, _, _ in pool]
    cids = [c["candidate_id"] for c in cands]
    hand_n = minmax([s for _, _, s in pool])
    texts = [candidate_text(c) for c in cands]

    from sentence_transformers import CrossEncoder
    ce = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    t = time.time()
    ce_n = minmax(ce.predict([(jd_full, tx) for tx in texts], show_progress_bar=False))
    print(f"  CE predict {time.time()-t:.0f}s\n", flush=True)

    print(f"BASELINE: train={base_tr:.4f}  test={base_te:.4f}\n", flush=True)
    print(f'{"w_ce":>6}{"train":>9}{"test":>9}{"test_vs_base":>14}')
    rows = []
    for w in SWEEP:
        final = (1 - w) * hand_n + w * ce_n
        order = sorted(range(len(cids)), key=lambda i: (-final[i], cids[i]))
        top100 = [cids[i] for i in order[:100]]
        tr = evaluate(top100, TRAIN).composite
        te = evaluate(top100, TEST).composite
        rows.append((w, tr, te))
        print(f"{w:>6.2f}{tr:>9.4f}{te:>9.4f}{te-base_te:>+14.4f}", flush=True)

    wstar = max(rows, key=lambda r: r[1])  # choose on TRAIN only
    print(f"\nw* chosen on TRAIN = {wstar[0]} (train {wstar[1]:.4f})")
    print(f"HOLDOUT (TEST) at w*: {wstar[2]:.4f} vs baseline {base_te:.4f}  =>  "
          f"validated delta {wstar[2]-base_te:+.4f}")
    print("VERDICT:", "GENERALIZES (adopt-worthy, weigh vs compliance cost)" if wstar[2] - base_te > 1e-4
          else "does NOT generalize (in-sample artifact — reject)")
    print("DONE")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
