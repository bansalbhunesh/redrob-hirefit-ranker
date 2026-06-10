#!/usr/bin/env python3
"""Phase 1.4: apply the pre-committed ambiguity rubric to every flagged profile.

Reads artifacts/honeypot_flagged.jsonl, evaluates each candidate's hard flags
against the rubric in docs/honeypot_audit.md (classification only -- no metric
peeking), and appends a per-candidate verdict table to the audit doc.

Verdicts: UPHELD (genuine honeypot) or AMBIGUOUS (plausible honest data-entry
explanation; cites the supporting fields).
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

# Profiles frequently self-report tenure in prose ("...with 4.8 years of
# experience..."). When that self-report matches the career history but the
# years_of_experience FIELD claims far more, the field is fabricated -- the
# decisive planted-honeypot tell found during manual review.
_STATED_YOE_RE = re.compile(r"with\s+([\d.]+)\s+years?\s+of\s+experience")

ROOT = Path(__file__).resolve().parents[1]
FLAGGED = ROOT / "artifacts" / "honeypot_flagged.jsonl"
DOC = ROOT / "docs" / "honeypot_audit.md"


def _parse_date(s):
    if not s:
        return None
    try:
        parts = str(s)[:10].split("-")
        return date(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 1)
    except (ValueError, IndexError):
        return None


def _overlap_months(career):
    """Total months of pairwise overlap between dated roles."""
    spans = []
    for j in career:
        start = _parse_date(j.get("start_date"))
        end = _parse_date(j.get("end_date")) or date(2026, 6, 8)
        if start and end and end > start:
            spans.append((start, end))
    total = 0
    for i in range(len(spans)):
        for k in range(i + 1, len(spans)):
            lo = max(spans[i][0], spans[k][0])
            hi = min(spans[i][1], spans[k][1])
            if hi > lo:
                total += (hi - lo).days // 30
    return total


def judge(candidate: dict, flags: list[str]) -> list[tuple[str, str, str]]:
    """Return (flag, verdict, evidence) per hard flag."""
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", []) or []
    skills = candidate.get("skills", []) or []
    out = []

    for flag in flags:
        if flag == "experience_timeline_exceeds_claim":
            yoe = float(profile.get("years_of_experience") or 0)
            months = sum(int(j.get("duration_months") or 0) for j in career)
            overshoot = months - int(yoe * 12)
            overlap = _overlap_months(career)
            if overlap >= overshoot - 30 and overlap > 0:
                out.append((flag, "AMBIGUOUS",
                            f"overshoot {overshoot}m vs {overlap}m of overlapping dated roles "
                            f"(concurrent jobs could honestly explain it)"))
            else:
                out.append((flag, "UPHELD",
                            f"claims {yoe:.0f}y but durations sum to {months}m "
                            f"(+{overshoot}m); dated overlaps only {overlap}m"))
        elif flag == "career_history_too_short_for_claimed_yoe":
            yoe = float(profile.get("years_of_experience") or 0)
            months = sum(int(j.get("duration_months") or 0) for j in career)
            n_roles = len(career)
            edu_end = max((int(e.get("end_year") or 0) for e in candidate.get("education", []) or []),
                          default=0)
            grad_consistent = edu_end and (2026 - edu_end) >= yoe - 1
            stated = None
            m = _STATED_YOE_RE.search(str(profile.get("summary") or ""))
            if m:
                stated = float(m.group(1))
            if stated is not None and abs(stated - months / 12) <= 1.5 and yoe - stated >= 3:
                out.append((flag, "UPHELD",
                            f"summary self-reports {stated}y (matches {months}m of history) "
                            f"but the YoE field claims {yoe:.1f}y -- fabricated field"))
            elif n_roles <= 2 and grad_consistent:
                out.append((flag, "AMBIGUOUS",
                            f"only {n_roles} roles listed and graduation {edu_end} is consistent "
                            f"with {yoe:.0f}y -- looks abbreviated, not fabricated"))
            else:
                out.append((flag, "UPHELD",
                            f"claims {yoe:.0f}y, history covers {months}m across {n_roles} roles; "
                            f"education ({edu_end or 'none'}) does not corroborate the claim"))
        elif flag == "expert_skill_zero_duration":
            zero_experts = [s for s in skills
                            if str(s.get("proficiency", "")).lower() == "expert"
                            and int(s.get("duration_months") or 0) == 0]
            # 1-3 endorsements is noise, not evidence of a curated import;
            # require a meaningful endorsement base (manual-review calibration).
            endorsed = [s for s in zero_experts if int(s.get("endorsements") or 0) >= 5]
            career_blob = " ".join(
                f"{j.get('title','')} {j.get('description','')}" for j in career).lower()
            corroborated = [s for s in zero_experts
                            if str(s.get("name", "")).lower() in career_blob]
            if len(endorsed) == len(zero_experts) and len(zero_experts) > 0:
                out.append((flag, "AMBIGUOUS",
                            f"all {len(zero_experts)} zero-duration expert skills carry "
                            f">=5 endorsements (looks like a fresh skill-list import)"))
            elif corroborated:
                out.append((flag, "AMBIGUOUS",
                            f"{len(corroborated)}/{len(zero_experts)} zero-duration expert skills "
                            f"corroborated in career text: "
                            f"{[s.get('name') for s in corroborated][:3]}"))
            else:
                out.append((flag, "UPHELD",
                            f"{len(zero_experts)} expert skills with 0 months, "
                            f"{len(endorsed)} endorsed, none corroborated by career history"))
        elif flag == "multiple_current_jobs":
            current = [j for j in career if j.get("is_current")]
            concurrentish = [j for j in current if any(
                t in str(j.get("title", "")).lower()
                for t in ("advisor", "consultant", "mentor", "lecturer", "maintainer",
                          "part-time", "freelance"))]
            if len(current) - len(concurrentish) <= 1:
                out.append((flag, "AMBIGUOUS",
                            f"{len(current)} current roles but {len(concurrentish)} are "
                            f"plausibly-concurrent types: "
                            f"{[j.get('title') for j in concurrentish][:3]}"))
            else:
                out.append((flag, "UPHELD",
                            f"{len(current)} concurrent full-time-looking roles: "
                            f"{[j.get('title') for j in current][:4]}"))
        elif flag == "impossible_education_timeline":
            bad = []
            for e in candidate.get("education", []) or []:
                start = int(e.get("start_year") or 0)
                end = int(e.get("end_year") or 0)
                if start and end and (end < start or start < 1970 or end > 2035):
                    bad.append((start, end))
            transposable = [
                (s, e) for s, e in bad if e < s and 2 <= (s - e) <= 6 and e >= 1970
            ]
            if bad and len(transposable) == len(bad):
                out.append((flag, "AMBIGUOUS",
                            f"degree years {bad} read as transposed start/end "
                            f"(swap gives a normal 2-6 year degree)"))
            else:
                out.append((flag, "UPHELD", f"impossible education years {bad}"))
        elif flag == "title_description_contradiction":
            title = profile.get("current_title")
            sizes = {str(j.get("company_size") or "?") for j in career}
            small_only = sizes <= {"1-10", "11-50", "?"}
            if small_only:
                out.append((flag, "AMBIGUOUS",
                            f"title '{title}' at small companies only ({sizes}) -- "
                            f"generalist-at-startup explanation possible"))
            else:
                out.append((flag, "UPHELD",
                            f"title '{title}' contradicts IR/ranking-heavy descriptions "
                            f"at non-tiny companies ({sizes})"))
        else:
            out.append((flag, "UPHELD", "no rubric exception applies"))
    return out


def main() -> None:
    records = [json.loads(line) for line in open(FLAGGED, encoding="utf-8")]
    rows = []
    ambiguous_by_class: dict[str, int] = {}
    upheld_by_class: dict[str, int] = {}
    for rec in records:
        for flag, verdict, evidence in judge(rec["profile"], rec["hard_flags"]):
            rows.append((rec["candidate_id"], flag, verdict, evidence))
            bucket = ambiguous_by_class if verdict == "AMBIGUOUS" else upheld_by_class
            bucket[flag] = bucket.get(flag, 0) + 1

    lines = ["## Verdicts", ""]
    lines.append(f"Rubric applied to all {len(records)} flagged candidates "
                 f"({len(rows)} flag instances). Summary:")
    lines.append("")
    lines.append("| flag class | upheld | ambiguous |")
    lines.append("|---|---|---|")
    for cls in sorted(set(list(upheld_by_class) + list(ambiguous_by_class))):
        lines.append(f"| `{cls}` | {upheld_by_class.get(cls, 0)} | {ambiguous_by_class.get(cls, 0)} |")
    lines.append("")
    lines.append("| candidate_id | flag | verdict | evidence |")
    lines.append("|---|---|---|---|")
    for cid, flag, verdict, evidence in rows:
        ev = evidence.replace("|", "/")
        lines.append(f"| {cid} | `{flag}` | **{verdict}** | {ev} |")
    lines.append("")

    doc = DOC.read_text(encoding="utf-8")
    marker = "## Verdicts"
    doc = doc[: doc.index(marker)] + "\n".join(lines) + "\n"
    DOC.write_text(doc, encoding="utf-8")
    amb_total = sum(ambiguous_by_class.values())
    print(f"verdicts: {sum(upheld_by_class.values())} upheld, {amb_total} ambiguous")
    for cls, n in ambiguous_by_class.items():
        print(f"  AMBIGUOUS x{n}: {cls}")


if __name__ == "__main__":
    main()
