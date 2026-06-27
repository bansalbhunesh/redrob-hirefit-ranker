"""Train the v2 LambdaMART ranker on label files, with k-fold CV.

Usage:
    PYTHONPATH=src python -m redrob_ranker_v2.train \
        --candidates candidates.jsonl \
        --labels docs/llm_judge_eval_labels.jsonl docs/llm_judge_eval_2_labels.jsonl \
        --out models/ltr_v2.txt --folds 5

The label files give relevance/tier for a subset of candidate ids; we build the
shared feature vector for exactly those (so the candidate pool is required), fit
``lambdarank`` (optimizing NDCG, the scored metric), report held-out composite
with the same harness the challenge uses, then refit on all labels and save.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import compute_features
from redrob_ranker.io import iter_candidates
from redrob_ranker.retrieval import retrieve_pool
from redrob_ranker.eval_harness import (
    LabelSet,
    evaluate,
    load_labels,
    merge_label_sets,
)

from redrob_ranker_v2.model import V2_FEATURES


def _load_relevance(label_paths: list[Path]) -> LabelSet:
    merged: LabelSet | None = None
    for p in label_paths:
        ls = load_labels(p)
        merged = ls if merged is None else merge_label_sets(merged, ls, name="train")
    assert merged is not None, "at least one label file required"
    return merged


def _feature_rows(candidates: list[dict]) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    """Return {candidate_id: feature_vector} and {candidate_id: gate}."""
    retrieval_scores, _ = retrieve_pool(candidates, 0)
    feats_by_id: dict[str, np.ndarray] = {}
    gate_by_id: dict[str, float] = {}
    for idx, cand in enumerate(candidates):
        f = compute_features(cand)
        vec = np.array(
            [f.values.get(n, 0.0) for n in FEATURE_NAMES] + [retrieval_scores.get(idx, 0.0)],
            dtype=np.float64,
        )
        feats_by_id[cand["candidate_id"]] = vec
        gate_by_id[cand["candidate_id"]] = f.honeypot_multiplier * f.disqualifier_multiplier
    return feats_by_id, gate_by_id


def _train_booster(X: np.ndarray, y: np.ndarray, seed: int = 0):
    import lightgbm as lgb

    dtrain = lgb.Dataset(X, label=y, group=[X.shape[0]], free_raw_data=False)
    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "ndcg_eval_at": [10, 50],
        "learning_rate": 0.03,
        "num_leaves": 8,
        "min_data_in_leaf": 8,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.9,
        "bagging_freq": 1,
        "lambdarank_truncation_level": 50,
        "seed": seed,
        "deterministic": True,
        "force_row_wise": True,
        "verbose": -1,
    }
    return lgb.train(params, dtrain, num_boost_round=150)


def _composite_on(ids: list[str], preds: np.ndarray, gates: np.ndarray, labels: LabelSet) -> float:
    lo, hi = float(preds.min()), float(preds.max())
    norm = (preds - lo) / (hi - lo) if hi > lo else np.zeros_like(preds)
    final = norm * gates
    order = sorted(range(len(ids)), key=lambda i: (-float(final[i]), ids[i]))
    ranked_ids = [ids[i] for i in order]
    return evaluate(ranked_ids, labels, unlabeled="exclude").composite


def main() -> None:
    ap = argparse.ArgumentParser(description="Train the v2 LambdaMART ranker.")
    ap.add_argument("--candidates", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path, nargs="+")
    ap.add_argument("--out", default=Path("models/ltr_v2.txt"), type=Path)
    ap.add_argument("--folds", default=5, type=int)
    args = ap.parse_args()

    labels = _load_relevance(args.labels)
    candidates = list(iter_candidates(args.candidates))
    feats_by_id, gate_by_id = _feature_rows(candidates)

    labeled_ids = [cid for cid in labels.tiers if cid in feats_by_id]
    if not labeled_ids:
        raise SystemExit(
            "No overlap between label ids and candidate pool — wrong --candidates file?"
        )
    X = np.vstack([feats_by_id[c] for c in labeled_ids])
    y = np.array([labels.gains.get(c, 0.0) for c in labeled_ids], dtype=np.float64)
    gates = np.array([gate_by_id[c] for c in labeled_ids], dtype=np.float64)
    print(f"Labeled candidates with features: {len(labeled_ids)} / {len(labels.tiers)} labels")

    # k-fold CV: train on k-1 folds, score held-out fold composite.
    rng = np.random.default_rng(0)
    perm = rng.permutation(len(labeled_ids))
    folds = np.array_split(perm, max(2, args.folds))
    comps: list[float] = []
    for fi, test_idx in enumerate(folds):
        train_idx = np.concatenate([f for j, f in enumerate(folds) if j != fi])
        booster = _train_booster(X[train_idx], y[train_idx])
        preds = booster.predict(X[test_idx])
        ids = [labeled_ids[i] for i in test_idx]
        comp = _composite_on(ids, preds, gates[test_idx], labels)
        comps.append(comp)
        print(f"  fold {fi+1}/{len(folds)}: held-out composite = {comp:.4f} (n={len(ids)})")
    print(f"CV mean composite: {np.mean(comps):.4f} +/- {np.std(comps):.4f}")

    # Refit on all labels and save.
    final = _train_booster(X, y)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    final.save_model(str(args.out))
    print(f"Saved model -> {args.out}")


if __name__ == "__main__":
    main()
