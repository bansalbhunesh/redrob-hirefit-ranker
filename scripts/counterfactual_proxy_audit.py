"""Experimental counterfactual/proxy audit for hiring-risk review.

This branch-only tool does not change ranking, calibration, or submission.csv.
It measures how much deterministic scores move under controlled profile edits
so a reviewer can separate legitimate job-fit signals from risky proxy signals.
"""

from __future__ import annotations

import argparse
import csv
import sys
from copy import deepcopy
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.features import compute_features, final_score
from redrob_ranker.io import iter_candidates


VariantBuilder = Callable[[dict], dict]

TRACKED_FEATURES = (
    "location_score",
    "education_score",
    "availability_score",
    "engagement_score",
    "responsiveness_score",
    "profile_quality",
)


def _with_profile(candidate: dict, **updates: object) -> dict:
    changed = deepcopy(candidate)
    changed.setdefault("profile", {}).update(updates)
    return changed


def _with_signals(candidate: dict, **updates: object) -> dict:
    changed = deepcopy(candidate)
    changed.setdefault("redrob_signals", {}).update(updates)
    return changed


def name_neutralized(candidate: dict) -> dict:
    changed = deepcopy(candidate)
    profile = changed.setdefault("profile", {})
    for key in ("anonymized_name", "name", "full_name", "first_name", "last_name"):
        if key in profile:
            profile[key] = "Neutral Candidate"
    profile.setdefault("anonymized_name", "Neutral Candidate")
    return changed


def location_undisclosed(candidate: dict) -> dict:
    return _with_profile(candidate, location="Undisclosed", country="")


def preferred_india_location(candidate: dict) -> dict:
    return _with_profile(candidate, location="Bengaluru, Karnataka", country="India")


def behavioral_neutral(candidate: dict) -> dict:
    return _with_signals(
        candidate,
        recruiter_response_rate=0.50,
        avg_response_time_hours=48,
        profile_views_received_30d=20,
        applications_submitted_30d=2,
        saved_by_recruiters_30d=2,
        search_appearance_30d=80,
        interview_completion_rate=0.70,
        offer_acceptance_rate=0.60,
    )


VARIANTS: tuple[tuple[str, VariantBuilder], ...] = (
    ("name_neutralized", name_neutralized),
    ("location_undisclosed", location_undisclosed),
    ("preferred_india_location", preferred_india_location),
    ("behavioral_neutral", behavioral_neutral),
)


def audit_candidate(candidate: dict, retrieval_score: float = 0.0) -> list[dict[str, object]]:
    base_features = compute_features(candidate)
    base_score = final_score(base_features, retrieval_score=retrieval_score)
    rows: list[dict[str, object]] = []

    for variant_name, build in VARIANTS:
        variant = build(candidate)
        variant_features = compute_features(variant)
        variant_score = final_score(variant_features, retrieval_score=retrieval_score)
        feature_deltas = {
            name: round(variant_features.values.get(name, 0.0) - base_features.values.get(name, 0.0), 6)
            for name in TRACKED_FEATURES
        }
        rows.append(
            {
                "candidate_id": str(candidate.get("candidate_id", "UNKNOWN")),
                "variant": variant_name,
                "base_score": round(base_score, 6),
                "variant_score": round(variant_score, 6),
                "score_delta": round(variant_score - base_score, 6),
                "behavioral_multiplier_delta": round(
                    variant_features.behavioral_multiplier - base_features.behavioral_multiplier,
                    6,
                ),
                "tracked_feature_deltas": feature_deltas,
                "base_flags": ",".join(base_features.flags),
                "variant_flags": ",".join(variant_features.flags),
            }
        )
    return rows


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "candidate_id",
                "variant",
                "base_score",
                "variant_score",
                "score_delta",
                "behavioral_multiplier_delta",
                "tracked_feature_deltas",
                "base_flags",
                "variant_flags",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a branch-only counterfactual proxy audit over candidate JSONL."
    )
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-candidates", type=int, default=200)
    parser.add_argument(
        "--retrieval-score",
        type=float,
        default=0.0,
        help="Fixed BM25/retrieval score used for all counterfactual comparisons.",
    )
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    for candidate in iter_candidates(args.candidates, max_candidates=args.max_candidates):
        rows.extend(audit_candidate(candidate, retrieval_score=args.retrieval_score))

    write_rows(args.out, rows)
    print(f"Wrote {len(rows)} counterfactual rows to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
