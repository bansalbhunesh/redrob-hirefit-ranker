"""Pure-NumPy inference for the loss-aggregation v3 research profile.

Seven small ExtraTrees heads predict independent development-label families.
The artifact stores only generic feature splits and leaf values: no candidate
IDs, public ranking positions, resume fingerprints, or competitor code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from redrob_ranker.features import CandidateFeatures

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "loss_aggregate_v3.npz"
MODEL_POOL_SIZE = 3000
MEMBERSHIP_LOCK = 100


def _minmax(values: np.ndarray) -> np.ndarray:
    lo = float(values.min())
    hi = float(values.max())
    if hi <= lo:
        return np.full_like(values, 0.5, dtype=np.float64)
    return (values - lo) / (hi - lo)


@lru_cache(maxsize=1)
def _artifact() -> dict[str, np.ndarray]:
    with np.load(MODEL_PATH, allow_pickle=False) as data:
        return {name: data[name] for name in data.files}


def _feature_matrix(
    pool: list[tuple[dict, CandidateFeatures, float]],
    feature_names: np.ndarray,
) -> np.ndarray:
    matrix = np.empty((len(pool), len(feature_names)), dtype=np.float64)
    for row, (_, features, _) in enumerate(pool):
        for col, raw_name in enumerate(feature_names):
            name = str(raw_name)
            if name == "hand":
                value = features.values.get("_main_score", 0.0)
            elif name == "behavior":
                value = features.behavior
            elif name == "logistics":
                value = features.logistics
            elif name == "role_fit":
                value = features.role_fit
            elif name == "ai_depth":
                value = features.ai_depth
            elif name == "production_evidence":
                value = features.production_evidence
            elif name == "honeypot_mult":
                value = features.honeypot_multiplier
            elif name == "disq_mult":
                value = features.disqualifier_multiplier
            else:
                value = features.values.get(name, 0.0)
            matrix[row, col] = float(value)
    return matrix


def _predict_heads(matrix: np.ndarray, data: dict[str, np.ndarray]) -> np.ndarray:
    """Evaluate every exported tree exactly, without a scikit-learn runtime."""

    tree_offsets = data["tree_offsets"]
    head_offsets = data["head_offsets"]
    predictions = np.empty((len(matrix), len(head_offsets) - 1), dtype=np.float64)

    for head in range(len(head_offsets) - 1):
        first_tree = int(head_offsets[head])
        last_tree = int(head_offsets[head + 1])
        total = np.zeros(len(matrix), dtype=np.float64)
        for tree_index in range(first_tree, last_tree):
            offset = int(tree_offsets[tree_index])
            node = np.zeros(len(matrix), dtype=np.int32)
            active = np.ones(len(matrix), dtype=bool)
            while active.any():
                absolute = offset + node
                leaf = data["feature"][absolute] < 0
                active &= ~leaf
                if not active.any():
                    break
                rows = np.flatnonzero(active)
                absolute = offset + node[rows]
                go_left = (
                    matrix[rows, data["feature"][absolute]]
                    <= data["threshold"][absolute]
                )
                node[rows] = np.where(
                    go_left,
                    data["children_left"][absolute],
                    data["children_right"][absolute],
                )
            total += data["value"][offset + node]
        predictions[:, head] = total / max(1, last_tree - first_tree)
    return predictions


def rerank_loss_aggregate(
    ranked: list[tuple[dict, CandidateFeatures, float]],
) -> list[tuple[dict, CandidateFeatures, float]]:
    """Reorder v2's top-100 membership with a gated seven-head rank hedge."""

    if not ranked:
        return ranked
    data = _artifact()
    v2_order = sorted(ranked, key=lambda item: (-item[2], item[0]["candidate_id"]))
    model_pool = sorted(
        ranked,
        key=lambda item: (
            -item[1].values.get("_main_score", 0.0),
            item[0]["candidate_id"],
        ),
    )[:MODEL_POOL_SIZE]

    matrix = _feature_matrix(model_pool, data["feature_names"])
    heads = _predict_heads(matrix, data)
    for head in range(heads.shape[1]):
        lo = float(data["head_min"][head])
        hi = float(data["head_max"][head])
        heads[:, head] = np.clip((heads[:, head] - lo) / (hi - lo), 0.0, 1.0)
    aggregate = _minmax(heads.mean(axis=1))

    gate = np.array(
        [item[1].honeypot_multiplier * item[1].disqualifier_multiplier for item in model_pool],
        dtype=np.float64,
    )
    v2_scores = np.array([item[2] for item in model_pool], dtype=np.float64)
    ungated_v2 = np.divide(v2_scores, gate, out=np.zeros_like(v2_scores), where=gate > 0)
    alpha = float(data["alpha"][0])
    model_scores = ((1.0 - alpha) * _minmax(ungated_v2) + alpha * aggregate) * gate
    v3_order = [
        model_pool[index]
        for index in np.lexsort(
            (
                np.array([item[0]["candidate_id"] for item in model_pool], dtype=object),
                -model_scores,
            )
        )
    ]

    membership_size = min(MEMBERSHIP_LOCK, len(v2_order))
    membership = v2_order[:membership_size]
    v2_rank = {item[0]["candidate_id"]: rank for rank, item in enumerate(membership, 1)}
    v3_rank = {
        item[0]["candidate_id"]: rank
        for rank, item in enumerate(v3_order[:MEMBERSHIP_LOCK], 1)
    }
    k = float(data["rrf_k"][0])
    v3_weight = float(data["rrf_v3_weight"][0])

    def rrf(item: tuple[dict, CandidateFeatures, float]) -> float:
        candidate_id = item[0]["candidate_id"]
        score = (1.0 - v3_weight) / (k + v2_rank[candidate_id])
        if candidate_id in v3_rank:
            score += v3_weight / (k + v3_rank[candidate_id])
        return score

    locked = sorted(membership, key=lambda item: (-rrf(item), item[0]["candidate_id"]))
    locked_ids = {item[0]["candidate_id"] for item in locked}
    result: list[tuple[dict, CandidateFeatures, float]] = []
    for item in locked:
        score = rrf(item)
        item[1].total = score
        result.append((item[0], item[1], score))
    result.extend(item for item in v2_order if item[0]["candidate_id"] not in locked_ids)
    return result
