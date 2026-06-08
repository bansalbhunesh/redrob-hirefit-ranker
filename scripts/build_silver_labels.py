#!/usr/bin/env python3
"""Build heuristic silver labels for local ranker evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.features import compute_features  # noqa: E402
from redrob_ranker.io import iter_candidates  # noqa: E402


def silver_label(candidate: dict) -> tuple[int, list[str]]:
    features = compute_features(candidate)
    values = features.values
    reasons: list[str] = []

    if features.honeypot_multiplier <= 0.0:
        return 0, ["hard_honeypot"]
    if values["keyword_stuffer_flag"] >= 0.5:
        return 1, ["keyword_stuffer"]

    score = 0
    if values["production_evidence"] >= 0.75:
        score += 1
        reasons.append("strong_production")
    if values["ir_ranking_experience"] >= 0.70:
        score += 1
        reasons.append("strong_ir_ranking")
    if values["core_skill_match"] >= 0.70 and values["skill_depth_score"] >= 0.65:
        score += 1
        reasons.append("deep_core_skills")
    if values["product_company_ratio"] >= 0.45:
        score += 1
        reasons.append("product_company")
    if values["yoe_fit_score"] >= 0.85 and values["senior_title_held"] >= 0.5:
        score += 1
        reasons.append("senior_experience")
    if values["location_score"] >= 0.65 and values["responsiveness_score"] >= 0.45:
        score += 1
        reasons.append("reachable_logistics")

    if features.disqualifier_multiplier < 0.7:
        score = max(0, score - 2)
        reasons.append("soft_disqualifier")
    elif features.disqualifier_multiplier < 1.0:
        score = max(0, score - 1)
        reasons.append("minor_disqualifier")

    if features.behavioral_multiplier < 0.65:
        score = max(0, score - 1)
        reasons.append("weak_behavior")

    return min(5, score), reasons or ["adjacent_fit"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate JD-rule silver labels.")
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-candidates", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.out.open("w", encoding="utf-8") as handle:
        for candidate in iter_candidates(args.candidates, max_candidates=args.max_candidates):
            label, reasons = silver_label(candidate)
            handle.write(
                json.dumps(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "silver_label": label,
                        "reasons": reasons,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            count += 1
    print(f"Wrote {count} silver labels to {args.out}")


if __name__ == "__main__":
    main()
