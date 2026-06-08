"""Offline silver-label ranking metrics for development and pitch defense."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


def dcg(labels: Sequence[float], k: int) -> float:
    total = 0.0
    for idx, label in enumerate(labels[:k], start=1):
        total += (2.0**float(label) - 1.0) / math.log2(idx + 1)
    return total


def ndcg_at_k(ranked_ids: Sequence[str], labels_by_id: Mapping[str, float], k: int) -> float:
    ranked_labels = [float(labels_by_id.get(cid, 0.0)) for cid in ranked_ids[:k]]
    ideal_labels = sorted((float(v) for v in labels_by_id.values()), reverse=True)[:k]
    ideal = dcg(ideal_labels, k)
    if ideal <= 0:
        return 0.0
    return dcg(ranked_labels, k) / ideal


def precision_at_k(ranked_ids: Sequence[str], labels_by_id: Mapping[str, float], k: int, threshold: float = 4.0) -> float:
    if k <= 0:
        return 0.0
    hits = sum(1 for cid in ranked_ids[:k] if float(labels_by_id.get(cid, 0.0)) >= threshold)
    return hits / min(k, max(1, len(ranked_ids)))


def average_precision(ranked_ids: Sequence[str], labels_by_id: Mapping[str, float], threshold: float = 4.0) -> float:
    relevant_total = sum(1 for value in labels_by_id.values() if float(value) >= threshold)
    if relevant_total == 0:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for idx, cid in enumerate(ranked_ids, start=1):
        if float(labels_by_id.get(cid, 0.0)) >= threshold:
            hits += 1
            precision_sum += hits / idx
    return precision_sum / relevant_total


def ranking_report(ranked_ids: Sequence[str], labels_by_id: Mapping[str, float]) -> dict[str, float]:
    return {
        "ndcg_at_10": ndcg_at_k(ranked_ids, labels_by_id, 10),
        "ndcg_at_50": ndcg_at_k(ranked_ids, labels_by_id, 50),
        "precision_at_10": precision_at_k(ranked_ids, labels_by_id, 10),
        "map": average_precision(ranked_ids, labels_by_id),
    }
