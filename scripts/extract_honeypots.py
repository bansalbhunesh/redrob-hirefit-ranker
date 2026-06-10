#!/usr/bin/env python3
"""Phase 1.4: extract hard-honeypot candidates and near-misses for audit.

Outputs:
  artifacts/honeypot_flagged.jsonl   -- every candidate with honeypot_multiplier == 0.0:
                                        {candidate_id, hard_flags, profile: <full candidate JSON>}
  artifacts/honeypot_nearmiss.jsonl  -- the 20 candidates closest to (but not over) exactly
                                        one honeypot threshold, for the false-NEGATIVE check
  docs/honeypot_audit.md             -- flag distribution + near-miss table appended into
                                        the pre-committed rubric document

Usage:
    PYTHONHASHSEED=0 python scripts/extract_honeypots.py [--max-candidates N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.features import (  # noqa: E402
    PADDED_CORE_SKILL_ALIASES,
    _NON_TARGET_PADDED,
    _has_boundary,
    _norm,
    compute_features,
)
from redrob_ranker.io import iter_candidates  # noqa: E402

HARD_FLAG_CLASSES = {
    "experience_timeline_exceeds_claim",
    "career_history_too_short_for_claimed_yoe",
    "expert_skill_zero_duration",
    "multiple_current_jobs",
    "impossible_education_timeline",
    "title_description_contradiction",
}

FLAGGED_OUT = ROOT / "artifacts" / "honeypot_flagged.jsonl"
NEARMISS_OUT = ROOT / "artifacts" / "honeypot_nearmiss.jsonl"
DOC = ROOT / "docs" / "honeypot_audit.md"


def _near_miss_signals(candidate: dict, values: dict[str, float]) -> list[tuple[str, float, str]]:
    """Return (flag_class, closeness 0..1 where 1 = at threshold, detail)."""
    out: list[tuple[str, float, str]] = []
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", []) or []
    skills = candidate.get("skills", []) or []

    yoe = float(profile.get("years_of_experience") or 0)
    expected = int(yoe * 12)
    months = sum(int(j.get("duration_months") or 0) for j in career)
    if expected:
        # fires at months > expected + 30; near-miss when within 12 months under
        gap = (expected + 30) - months
        if 0 <= gap <= 12:
            out.append(("experience_timeline_exceeds_claim", 1 - gap / 12,
                        f"career {months}m vs claim {expected}m (+30 grace); {gap}m under threshold"))

    if yoe >= 5 and career and expected:
        ratio = months / expected
        # fires at ratio < 0.45; near-miss in [0.45, 0.55)
        if 0.45 <= ratio < 0.55:
            out.append(("career_history_too_short_for_claimed_yoe", 1 - (ratio - 0.45) / 0.10,
                        f"history ratio {ratio:.2f} (fires below 0.45)"))

    expert_zero_core = expert_zero_any = 0
    for skill in skills:
        if str(skill.get("proficiency") or "").lower() != "expert":
            continue
        if int(skill.get("duration_months") or 0) != 0:
            continue
        expert_zero_any += 1
        if _has_boundary(PADDED_CORE_SKILL_ALIASES, _norm(skill.get("name"))):
            expert_zero_core += 1
    # fires at core >= 2 or any >= 5
    if expert_zero_core == 1:
        out.append(("expert_skill_zero_duration", 1.0, "1 core expert-zero skill (fires at 2)"))
    elif expert_zero_any == 4:
        out.append(("expert_skill_zero_duration", 0.9, "4 expert-zero skills (fires at 5)"))

    current = sum(1 for j in career if j.get("is_current"))
    if current == 2:  # fires at > 2
        out.append(("multiple_current_jobs", 1.0, "2 current jobs (fires at 3)"))

    for edu in candidate.get("education", []) or []:
        start = int(edu.get("start_year") or 0)
        end = int(edu.get("end_year") or 0)
        if start and end and end >= start:
            if start == end:
                out.append(("impossible_education_timeline", 0.8,
                            f"degenerate single-year degree {start}-{end}"))
            elif 1970 <= start <= 1972 or 2033 <= end <= 2035:
                out.append(("impossible_education_timeline", 0.6,
                            f"edge-of-range years {start}-{end}"))

    # fires at non-target title AND ir_ranking_experience >= 0.45
    title = _norm(profile.get("current_title"))
    ir = values.get("ir_ranking_experience", 0.0)
    if _has_boundary(_NON_TARGET_PADDED, title) and 0.30 <= ir < 0.45:
        out.append(("title_description_contradiction", (ir - 0.30) / 0.15,
                    f"non-target title '{profile.get('current_title')}' with ir_ranking={ir:.2f} (fires at 0.45)"))

    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=Path, default=ROOT / "candidates.jsonl")
    ap.add_argument("--max-candidates", type=int, default=None)
    args = ap.parse_args()

    flagged: list[dict] = []
    near: list[tuple[float, str, dict, list]] = []
    flag_counts: dict[str, int] = {}

    for candidate in iter_candidates(args.candidates, max_candidates=args.max_candidates):
        features = compute_features(candidate)
        hard = [f for f in features.flags if f in HARD_FLAG_CLASSES]
        if features.honeypot_multiplier <= 0.0:
            flagged.append({
                "candidate_id": candidate["candidate_id"],
                "hard_flags": hard,
                "profile": candidate,
            })
            for f in hard:
                flag_counts[f] = flag_counts.get(f, 0) + 1
            continue
        signals = _near_miss_signals(candidate, features.values)
        if len(signals) == 1:  # exactly one condition almost met
            cls, closeness, detail = signals[0]
            # also require title contradiction near-miss handled implicitly; ir value needs features
            near.append((closeness, cls, candidate, [detail]))

    near.sort(key=lambda t: (-t[0], t[2]["candidate_id"]))
    near20 = near[:20]

    FLAGGED_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(FLAGGED_OUT, "w", encoding="utf-8") as f:
        for rec in flagged:
            f.write(json.dumps(rec) + "\n")
    with open(NEARMISS_OUT, "w", encoding="utf-8") as f:
        for closeness, cls, candidate, details in near20:
            f.write(json.dumps({
                "candidate_id": candidate["candidate_id"],
                "near_class": cls,
                "closeness": round(closeness, 3),
                "detail": details[0],
                "profile": candidate,
            }) + "\n")

    lines = ["## Flagged population", ""]
    lines.append(f"Hard honeypots (multiplier 0.0): **{len(flagged)}** "
                 f"(full records: `artifacts/honeypot_flagged.jsonl`).")
    lines.append("")
    lines.append("| flag class | count |")
    lines.append("|---|---|")
    for cls in sorted(flag_counts, key=lambda c: -flag_counts[c]):
        lines.append(f"| `{cls}` | {flag_counts[cls]} |")
    multi = sum(1 for r in flagged if len(r["hard_flags"]) > 1)
    lines.append("")
    lines.append(f"Candidates with 2+ hard flags: **{multi}** of {len(flagged)}.")
    lines.append("")
    lines.append("## Near-miss false-negative check")
    lines.append("")
    lines.append(f"20 closest near-misses (exactly one condition almost met) in "
                 f"`artifacts/honeypot_nearmiss.jsonl`:")
    lines.append("")
    lines.append("| candidate_id | near class | closeness | detail |")
    lines.append("|---|---|---|---|")
    for closeness, cls, candidate, details in near20:
        lines.append(f"| {candidate['candidate_id']} | `{cls}` | {closeness:.2f} | {details[0]} |")
    lines.append("")
    lines.append("## Verdicts")
    lines.append("")
    lines.append("_(per-candidate verdict table; manual verification pass pending user review)_")

    doc = DOC.read_text(encoding="utf-8")
    marker = "## Flagged population"
    doc = doc[: doc.index(marker)] + "\n".join(lines) + "\n"
    DOC.write_text(doc, encoding="utf-8")
    print(f"flagged={len(flagged)} near-misses={len(near20)} (pool of {len(near)}) "
          f"-> {FLAGGED_OUT.name}, {NEARMISS_OUT.name}, {DOC.name}")


if __name__ == "__main__":
    main()
