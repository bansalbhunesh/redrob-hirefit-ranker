"""Train and export the candidate-ID-free loss-aggregate-v3 tree artifact.

Prerequisite: run ``experiments/_build_pool.py`` to create the ignored top-3000
feature cache. Scikit-learn is research-only; runtime inference is pure NumPy.
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from public_field_benchmark import _label_sets  # noqa: E402

TREES_PER_HEAD = 30
MAX_DEPTH = 6
MIN_LEAF = 3
MAX_FEATURES = 0.7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=Path, default=ROOT / "experiments" / "_pool.pkl")
    parser.add_argument("--labels-root", type=Path, required=True)
    parser.add_argument("--reviewer-csv", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "models" / "loss_aggregate_v3.npz",
    )
    return parser.parse_args()


def _matrix(records: list[dict]) -> tuple[np.ndarray, list[str], list[str]]:
    feature_names = sorted(records[0]["values"])
    extras = [
        "hand",
        "behavior",
        "logistics",
        "role_fit",
        "ai_depth",
        "production_evidence",
        "honeypot_mult",
        "disq_mult",
    ]
    matrix = np.array(
        [
            [record["values"].get(name, 0.0) for name in feature_names]
            + [record[name] for name in extras]
            for record in records
        ],
        dtype=np.float64,
    )
    return matrix, feature_names, extras


def _train(records: list[dict], matrix: np.ndarray, label_sets: list) -> list:
    candidate_index = {record["cid"]: index for index, record in enumerate(records)}
    candidate_ids = np.array([record["cid"] for record in records], dtype=object)
    models = []
    for head, labels in enumerate(label_sets[:7]):
        rows = np.array([candidate_index[cid] for cid in labels.gains if cid in candidate_index])
        target = np.array([labels.gains[candidate_ids[index]] for index in rows])
        model = ExtraTreesRegressor(
            n_estimators=TREES_PER_HEAD,
            max_depth=MAX_DEPTH,
            min_samples_leaf=MIN_LEAF,
            max_features=MAX_FEATURES,
            n_jobs=-1,
            random_state=100 + head,
        )
        model.fit(matrix[rows], target)
        models.append(model)
    return models


def _export(
    models: list,
    matrix: np.ndarray,
    feature_names: list[str],
    extras: list[str],
    out: Path,
) -> None:
    children_left: list[int] = []
    children_right: list[int] = []
    feature: list[int] = []
    threshold: list[float] = []
    value: list[float] = []
    tree_offsets = [0]
    head_offsets = [0]
    head_min: list[float] = []
    head_max: list[float] = []

    for model in models:
        prediction = model.predict(matrix)
        # Parallel forest reduction can differ at ~1e-15 across runs. These
        # extrema are normalization metadata, so 12-decimal quantization makes
        # the exported artifact bit-stable without changing any tree decision.
        head_min.append(round(float(prediction.min()), 12))
        head_max.append(round(float(prediction.max()), 12))
        for estimator in model.estimators_:
            tree = estimator.tree_
            children_left.extend(tree.children_left.tolist())
            children_right.extend(tree.children_right.tolist())
            feature.extend(tree.feature.tolist())
            threshold.extend(tree.threshold.tolist())
            value.extend(tree.value[:, 0, 0].tolist())
            tree_offsets.append(len(children_left))
        head_offsets.append(len(tree_offsets) - 1)

    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        children_left=np.array(children_left, dtype=np.int32),
        children_right=np.array(children_right, dtype=np.int32),
        feature=np.array(feature, dtype=np.int16),
        threshold=np.array(threshold, dtype=np.float64),
        value=np.array(value, dtype=np.float64),
        tree_offsets=np.array(tree_offsets, dtype=np.int32),
        head_offsets=np.array(head_offsets, dtype=np.int16),
        head_min=np.array(head_min, dtype=np.float64),
        head_max=np.array(head_max, dtype=np.float64),
        feature_names=np.array(feature_names + extras),
        alpha=np.array([0.3625], dtype=np.float64),
        rrf_k=np.array([60.0], dtype=np.float64),
        rrf_v3_weight=np.array([0.27], dtype=np.float64),
        training=np.array(["7x30 ExtraTrees depth=6 leaf=3 max_features=.7 seeds=100..106"]),
    )
    print(f"wrote {out} ({out.stat().st_size:,} bytes; no candidate IDs)")


def main() -> None:
    args = parse_args()
    with args.pool.open("rb") as handle:
        records = pickle.load(handle)["recs"]
    matrix, feature_names, extras = _matrix(records)
    _, label_sets = _label_sets(args.labels_root, args.reviewer_csv)
    models = _train(records, matrix, label_sets)
    _export(models, matrix, feature_names, extras, args.out)


if __name__ == "__main__":
    main()
