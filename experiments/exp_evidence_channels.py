"""Test the new evidence channels: are they INDEPENDENT of the existing features, and
do they survive nested holdout? Independence is the crux -- a channel that correlates
~0.9 with the hand score carries no new information no matter how principled.
"""
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels, minmax, gate_repeat  # noqa: E402
from evidence_channels import BM25F, requirement_features  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402


def main():
    recs, base_ids = load_pool()
    hand = np.array([r["hand"] for r in recs])
    bm25_flat = np.array([r["values"].get("bm25_score", 0.0) for r in recs])

    print("building BM25F + counterfactual over 3000 pool...", flush=True)
    bf = BM25F([r["cand"] for r in recs])
    bm25f, ssd, var = bf.counterfactual()

    print("building requirement->evidence features...", flush=True)
    reqfeats = [requirement_features(r["cand"]) for r in recs]
    keys = list(reqfeats[0])
    reqmat = {k: np.array([rf[k] for rf in reqfeats]) for k in keys}

    channels = {
        "BM25F": bm25f,
        "counterfactual_robustness(1-ssd)": 1.0 - ssd,
        **{k: reqmat[k] for k in keys},
    }

    print(f"\n{'channel':<34}{'corr(hand)':>11}{'corr(bm25flat)':>15}")
    for name, v in channels.items():
        ch = float(spearmanr(v, hand).correlation)
        cb = float(spearmanr(v, bm25_flat).correlation)
        print(f"{name:<34}{ch:>11.3f}{cb:>15.3f}")

    print("\nnested repeated-holdout (R=20) as a blended signal vs golden:")
    for name, v in channels.items():
        # skip degenerate (no variance)
        if np.std(v) < 1e-9:
            print(f"{name:<34} (constant, skipped)")
            continue
        gate_repeat(recs, base_ids, v, name, mode="blend", R=20,
                    weights=[0.05, 0.10, 0.15, 0.20, 0.30])


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
