"""Shared evaluation harness for all offline experiments.

Single source of truth for scoring a submission ordering against one or more
label files with the challenge composite:

    0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10

Used by scripts/sensitivity_sweep.py, scripts/ablation_study.py, and
scripts/evaluate_independent.py so every number in the docs comes from the
same code path.

Unlabeled-candidate policy is explicit and configurable:
  - "exclude" (pre-registered default for experiments): candidates without a
    label are dropped from the ranking before metric computation; coverage is
    reported so low-coverage results are visibly less trustworthy.
  - "zero": legacy behavior of scripts/evaluate_independent.py — missing
    labels count as relevance 0. Never the default for experiments, kept for
    backward comparison with previously published numbers.

P@10 uses tier>=3 ("relevant"); MAP is binary at tier>=3 with AP computed over
the submitted ranking (documented approximation; relative deltas between
ranker variants are what matter).
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from redrob_ranker.eval import dcg

RELEVANT_TIER = 3.0
COMPOSITE_WEIGHTS = {"ndcg10": 0.50, "ndcg50": 0.30, "map": 0.15, "p10": 0.05}


@dataclass(frozen=True, slots=True)
class LabelSet:
    name: str
    tiers: dict[str, float]   # integer tiers, for binary P@10 / MAP
    gains: dict[str, float]   # continuous relevance if present, else tier


@dataclass(frozen=True, slots=True)
class EvalResult:
    label_set: str
    policy: str
    ndcg10: float
    ndcg50: float
    map: float
    p10: float
    composite: float
    coverage: float           # fraction of submitted ids that had a label
    n_ranked_scored: int      # ids actually used for metrics after policy
    n_labels: int

    def as_row(self) -> dict[str, float | str | int]:
        return {
            "label_set": self.label_set,
            "policy": self.policy,
            "ndcg10": round(self.ndcg10, 4),
            "ndcg50": round(self.ndcg50, 4),
            "map": round(self.map, 4),
            "p10": round(self.p10, 4),
            "composite": round(self.composite, 4),
            "coverage": round(self.coverage, 4),
            "n_ranked_scored": self.n_ranked_scored,
            "n_labels": self.n_labels,
        }


def load_submission(path: Path) -> list[str]:
    """Return candidate_ids ordered by rank from a submission CSV."""
    with open(path, encoding="utf-8-sig", newline="") as handle:
        rows = sorted(csv.DictReader(handle), key=lambda r: int(r["rank"]))
    return [r["candidate_id"] for r in rows]


def load_labels(path: Path, name: str | None = None) -> LabelSet:
    """Load a JSONL label file with {"candidate_id", "tier"[, "relevance"]}."""
    tiers: dict[str, float] = {}
    gains: dict[str, float] = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        cid = rec["candidate_id"]
        tier = float(rec.get("tier", rec.get("silver_label", 0)))
        tiers[cid] = tier
        gains[cid] = float(rec.get("relevance", tier))
    return LabelSet(name=name or Path(path).stem, tiers=tiers, gains=gains)


def merge_label_sets(base: LabelSet, extra: LabelSet, name: str | None = None) -> LabelSet:
    """Overlay `extra` labels onto `base` (extra wins on conflict)."""
    return LabelSet(
        name=name or f"{base.name}+{extra.name}",
        tiers={**base.tiers, **extra.tiers},
        gains={**base.gains, **extra.gains},
    )


def _ndcg(ranked: list[str], gains: dict[str, float], k: int) -> float:
    ranked_gains = [float(gains.get(cid, 0.0)) for cid in ranked[:k]]
    ideal = sorted((float(v) for v in gains.values()), reverse=True)[:k]
    ideal_dcg = dcg(ideal, k)
    if ideal_dcg <= 0:
        return 0.0
    return dcg(ranked_gains, k) / ideal_dcg


def precision_at_k(ranked: list[str], tiers: dict[str, float], k: int, thr: float = RELEVANT_TIER) -> float:
    if k <= 0 or not ranked:
        return 0.0
    return sum(1 for cid in ranked[:k] if tiers.get(cid, 0.0) >= thr) / k


def average_precision(ranked: list[str], tiers: dict[str, float], thr: float = RELEVANT_TIER) -> float:
    total_relevant = sum(1 for v in tiers.values() if v >= thr)
    if total_relevant == 0:
        return 0.0
    denom = min(total_relevant, len(ranked)) if ranked else total_relevant
    hits = 0
    psum = 0.0
    for i, cid in enumerate(ranked, start=1):
        if tiers.get(cid, 0.0) >= thr:
            hits += 1
            psum += hits / i
    return psum / denom


def evaluate(
    ranked_ids: list[str],
    labels: LabelSet,
    unlabeled: str = "exclude",
) -> EvalResult:
    """Score one ordering against one label set under an explicit policy."""
    if unlabeled not in {"exclude", "zero"}:
        raise ValueError(f"unknown unlabeled policy: {unlabeled!r}")

    labeled = [cid for cid in ranked_ids if cid in labels.tiers]
    coverage = (len(labeled) / len(ranked_ids)) if ranked_ids else 0.0
    scored = labeled if unlabeled == "exclude" else list(ranked_ids)

    ndcg10 = _ndcg(scored, labels.gains, 10)
    ndcg50 = _ndcg(scored, labels.gains, 50)
    mapv = average_precision(scored, labels.tiers)
    p10 = precision_at_k(scored, labels.tiers, 10)
    composite = (
        COMPOSITE_WEIGHTS["ndcg10"] * ndcg10
        + COMPOSITE_WEIGHTS["ndcg50"] * ndcg50
        + COMPOSITE_WEIGHTS["map"] * mapv
        + COMPOSITE_WEIGHTS["p10"] * p10
    )
    return EvalResult(
        label_set=labels.name,
        policy=unlabeled,
        ndcg10=ndcg10,
        ndcg50=ndcg50,
        map=mapv,
        p10=p10,
        composite=composite,
        coverage=coverage,
        n_ranked_scored=len(scored),
        n_labels=len(labels.tiers),
    )


def evaluate_many(
    ranked_ids: list[str],
    label_sets: list[LabelSet],
    unlabeled: str = "exclude",
) -> tuple[list[EvalResult], float]:
    """Score against several label sets; returns results and mean composite."""
    results = [evaluate(ranked_ids, ls, unlabeled=unlabeled) for ls in label_sets]
    mean_composite = sum(r.composite for r in results) / len(results) if results else 0.0
    return results, mean_composite


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Score a submission with the shared harness.")
    ap.add_argument("--submission", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path, nargs="+")
    ap.add_argument("--unlabeled", choices=["exclude", "zero"], default="exclude")
    args = ap.parse_args()

    ranked = load_submission(args.submission)
    sets = [load_labels(p) for p in args.labels]
    results, mean_composite = evaluate_many(ranked, sets, unlabeled=args.unlabeled)
    for r in results:
        row = r.as_row()
        print(
            f"{row['label_set']:<32} policy={row['policy']:<7} "
            f"NDCG@10={row['ndcg10']:.4f} NDCG@50={row['ndcg50']:.4f} "
            f"MAP={row['map']:.4f} P@10={row['p10']:.4f} "
            f"composite={row['composite']:.4f} coverage={row['coverage']:.1%}"
        )
    if len(results) > 1:
        print(f"mean composite: {mean_composite:.4f}")


if __name__ == "__main__":
    main()
