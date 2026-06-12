#!/usr/bin/env python3
"""Print top-ranked candidates and proxy tiers for a multi-JD role.

This is a tuning/debug helper for the lab branch. It uses the same role rubrics
as scripts/multi_jd_generalization_eval.py and prints enough feature columns to
see why the ranker is losing to a keyword baseline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.io import iter_candidates  # noqa: E402
from redrob_ranker.jd_compiler import compile_jd  # noqa: E402
from redrob_ranker.pipeline import RankerConfig, rank_candidates  # noqa: E402
from scripts.multi_jd_generalization_eval import (  # noqa: E402
    REFERENCE_ROLES,
    build_labels,
    keyword_baseline_order,
)


def _profile(candidate: dict) -> dict:
    return candidate.get("profile") or {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--role", required=True, choices=sorted(REFERENCE_ROLES))
    parser.add_argument("--max-candidates", type=int, default=5000)
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--backend", default="bm25s")
    args = parser.parse_args()

    candidates = list(iter_candidates(args.candidates, max_candidates=args.max_candidates))
    spec = REFERENCE_ROLES[args.role]
    labels = build_labels(candidates, args.role, spec)
    compiled = compile_jd(str(spec["jd"]), source=f"diagnose:{args.role}")
    ranked, used_backend = rank_candidates(
        candidates,
        RankerConfig(
            candidate_pool_size=0,
            bm25_backend=args.backend,
            workers=1,
            jd=compiled,
            apply_calibration=False,
        ),
    )
    by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    ranked_by_id = {candidate["candidate_id"]: (features, score) for candidate, features, score in ranked}

    print(f"role={args.role} candidates={len(candidates)} bm25={used_backend}")
    print("\nHireFit top")
    print("rank id tier score title yoe beh core kw title_fit role_ev prod yoe_fit flags")
    for rank, (candidate, features, score) in enumerate(ranked[: args.top], start=1):
        profile = _profile(candidate)
        values = features.values
        print(
            rank,
            candidate["candidate_id"],
            int(labels.tiers[candidate["candidate_id"]]),
            round(score, 4),
            repr(profile.get("current_title")),
            profile.get("years_of_experience"),
            round(features.behavioral_multiplier, 3),
            round(values["core_skill_match"], 3),
            round(values["jd_keyword_coverage_score"], 3),
            round(values["title_match_score"], 3),
            round(values["ir_ranking_experience"], 3),
            round(values["production_evidence"], 3),
            round(values["yoe_fit_score"], 3),
            ",".join(features.flags[:4]) or "-",
        )

    print("\nKeyword top")
    for rank, cid in enumerate(keyword_baseline_order(candidates, spec)[: args.top], start=1):
        candidate = by_id[cid]
        profile = _profile(candidate)
        features, score = ranked_by_id[cid]
        values = features.values
        print(
            rank,
            cid,
            int(labels.tiers[cid]),
            round(score, 4),
            repr(profile.get("current_title")),
            profile.get("years_of_experience"),
            round(features.behavioral_multiplier, 3),
            round(values["core_skill_match"], 3),
            round(values["jd_keyword_coverage_score"], 3),
            round(values["title_match_score"], 3),
            round(values["ir_ranking_experience"], 3),
            round(values["production_evidence"], 3),
            round(values["yoe_fit_score"], 3),
            ",".join(features.flags[:4]) or "-",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
