#!/usr/bin/env python3
"""
Train LightGBM LambdaMART re-ranker.

Optimizes NDCG directly. Trains on pessimistic labels.
Validates on frozen blind test (never trains on it).
"""

import json
import numpy as np
import lightgbm as lgb
from pathlib import Path
from typing import List, Tuple

# ================================================================
# LOAD DATA
# ================================================================
def load_jsonl(path: str) -> List[dict]:
    """Load jsonl data."""
    data = []
    with open(path) as f:
        for line in f:
            data.append(json.loads(line))
    return data

def prepare_lgb_data(data: List[dict]):
    """Convert to LightGBM Dataset format."""
    # Feature names (must match exactly)
    feature_names = [
        "bm25_score", "core_skill_match", "nice_skill_match", "skill_depth_score",
        "endorsement_trust", "assessment_score_avg", "github_signal",
        "product_company_ratio", "ir_ranking_experience", "production_evidence",
        "senior_title_held", "career_trajectory_score", "scale_signal",
        "code_writing_recent", "yoe_fit_score", "education_score",
        "ml_ai_tenure_score", "open_source_signal", "location_score",
        "relocation_willing", "notice_period_score", "disqualifier_flag",
        "keyword_stuffer_flag", "consulting_only_flag", "honeypot_multiplier",
        "title_match_score", "backend_depth_score", "data_bi_depth_score",
    ]

    X = []
    y = []

    for row in data:
        feats = row["features"]
        vec = [feats.get(name, 0.0) for name in feature_names]
        X.append(vec)
        # LambdaMART expects integer relevance labels (e.g., 0-30)
        y.append(int(row["pessimistic_label"] * 30))

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32), feature_names

# ================================================================
# COMPUTE NDCG
# ================================================================
def dcg_at_k(relevances: np.ndarray, k: int) -> float:
    """Compute DCG@k."""
    relevances = np.asarray(relevances, dtype=float)[:k]
    if relevances.size == 0:
        return 0.0
    return np.sum(relevances / np.log2(np.arange(2, relevances.size + 2)))

def ndcg_at_k(relevances: np.ndarray, k: int) -> float:
    """Compute NDCG@k."""
    ideal_relevances = np.sort(relevances)[::-1]
    ideal_dcg = dcg_at_k(ideal_relevances, k)
    if ideal_dcg == 0:
        return 0.0
    return dcg_at_k(relevances, k) / ideal_dcg

# ================================================================
# TRAIN
# ================================================================
def train_model():
    print("Loading training data...")
    train_data = load_jsonl("training_data_train.jsonl")
    val_data = load_jsonl("training_data_val.jsonl")

    X_train, y_train, feature_names = prepare_lgb_data(train_data)
    X_val, y_val, _ = prepare_lgb_data(val_data)

    print(f"Train: {len(X_train)} samples, {len(feature_names)} features")
    print(f"Val: {len(X_val)} samples")

    # For pointwise ranking (LambdaMART needs query groups)
    # In our case, each "query" is the JD, and all candidates are in one group
    # For simplicity, we use pointwise with NDCG eval
    group_train = np.array([len(X_train)], dtype=np.int32)
    group_val = np.array([len(X_val)], dtype=np.int32)

    train_dataset = lgb.Dataset(X_train, label=y_train, group=group_train, feature_name=feature_names)
    val_dataset = lgb.Dataset(X_val, label=y_val, group=group_val, reference=train_dataset,
                              feature_name=feature_names)

    params = {
        "objective": "lambdarank",
        "metric": ["ndcg", "auc"],
        "ndcg_eval_at": [10, 50, 100],
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": 6,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "min_data_in_leaf": 20,
        "verbose": -1,
        "num_threads": 4,
        "boosting_type": "gbdt",
    }

    print("\nTraining LightGBM LambdaMART...")
    model = lgb.train(
        params,
        train_dataset,
        num_boost_round=300,
        valid_sets=[train_dataset, val_dataset],
        valid_names=["train", "val"],
        callbacks=[
            lgb.early_stopping(stopping_rounds=30),
            lgb.log_evaluation(period=20)
        ]
    )

    print(f"\nBest iteration: {model.best_iteration}")
    print(f"Best score: {model.best_score}")

    # Save model
    model.save_model("reranker_lgbm.txt")
    print("Saved: reranker_lgbm.txt")

    # Feature importance
    print("\nFeature Importance (gain):")
    importance = model.feature_importance(importance_type="gain")
    for name, imp in sorted(zip(feature_names, importance), key=lambda x: -x[1]):
        print(f"  {name:30s}: {imp:10.1f}")

    return model

# ================================================================
# EVALUATE ON FROZEN BLIND TEST
# ================================================================
def evaluate_blind(model):
    """Evaluate on frozen blind test. NEVER train on this."""
    print("\n=== FROZEN BLIND TEST EVALUATION ===")
    blind_data = load_jsonl("blind_test_frozen.jsonl")
    X_blind, y_blind, _ = prepare_lgb_data(blind_data)

    preds = model.predict(X_blind)

    # NDCG@10
    ndcg_10 = ndcg_at_k(y_blind[np.argsort(-preds)], 10)
    ndcg_50 = ndcg_at_k(y_blind[np.argsort(-preds)], 50)

    # Pearson correlation
    pearson = np.corrcoef(preds, y_blind)[0, 1]

    print(f"NDCG@10: {ndcg_10:.4f}")
    print(f"NDCG@50: {ndcg_50:.4f}")
    print(f"Pearson: {pearson:.4f}")
    print(f"Samples: {len(y_blind)}")
    print("NOTE: This is the ONLY time you look at blind test metrics.")
    print("      Do NOT use this for hyperparameter tuning.")

    return {"ndcg@10": ndcg_10, "ndcg@50": ndcg_50, "pearson": pearson}

# ================================================================
# MAIN
# ================================================================
def main():
    model = train_model()
    evaluate_blind(model)
    print("\nDone. Model ready for integration.")

if __name__ == "__main__":
    main()
