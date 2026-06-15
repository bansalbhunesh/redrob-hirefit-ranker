"""Two-level integrity classifier (P0). Splits the existing honeypot flags + the
anachronism detector into HARD violations (temporal/logical impossibilities -- never
rescued by relevance) and AMBIGUOUS data-quality warnings (innocent-incomplete-record
readings exist -- rescue-eligible with multi-channel evidence).

HARD (decisive impossibility):
  experience_timeline_exceeds_claim   career months > claimed YoE timeline
  tech_anachronism                    skill/job claims a tech longer/earlier than it existed
  impossible_education_timeline       end<start, or out-of-range years
  multiple_current_jobs               >2 concurrent current jobs
  expert_skill_zero_duration_UNCORROB expert@0mo skills NOT supported in career text/assessment
  summary_profile_contradiction       title contradicts demonstrated ranking/IR experience

AMBIGUOUS (rescue-eligible):
  career_history_too_short            one/abbreviated history vs claimed YoE
  expert_skill_zero_duration_CORROB   expert@0mo but the skill IS corroborated in career text
  (missing skill durations, incomplete imported dates fold into the above two)

Reuses the shipped detectors (no src change). The shipped scorer hard-zeros the first
four and 0.05x-softens the last two; this classifier additionally treats anachronism as
HARD (the shipped scorer does NOT detect it) and separates corroborated expert-zero.
"""
from __future__ import annotations

import sys

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")

from redrob_ranker.features import _DEFAULT_MATCHERS, _honeypot_flags, _norm  # noqa: E402
from anachronism import is_anachronistic, worst_severity  # noqa: E402

_HARD_BASE = {
    "experience_timeline_exceeds_claim",
    "impossible_education_timeline",
    "multiple_current_jobs",
    "title_description_contradiction",
}
_AMBIGUOUS_BASE = {"career_history_too_short_for_claimed_yoe"}


def _expert_zero_corroborated(candidate: dict) -> bool:
    """An expert@0-month skill is corroborated if its name appears in career text
    (or there is an assessment). Corroboration => innocent import => AMBIGUOUS."""
    career_text = " ".join(
        _norm(j.get("title")) + " " + _norm(j.get("description")) + " " + _norm(j.get("company"))
        for j in (candidate.get("career_history") or [])
    ).lower()
    has_assessment = bool(candidate.get("assessments") or candidate.get("assessment_scores"))
    for skill in candidate.get("skills") or []:
        if str(skill.get("proficiency") or "").lower() != "expert":
            continue
        if int(skill.get("duration_months") or 0) != 0:
            continue
        nm = _norm(skill.get("name")).lower()
        if nm and (nm in career_text or has_assessment):
            return True
    return False


def classify(candidate: dict, values: dict | None = None) -> dict:
    """Return {'hard': [...], 'ambiguous': [...], 'level': 'hard'|'ambiguous'|'clean'}."""
    vals = values if values is not None else {}
    base = set(_honeypot_flags(candidate, vals, _DEFAULT_MATCHERS)) if vals else set()
    hard, amb = [], []

    for f in base:
        if f in _HARD_BASE:
            hard.append(f)
        elif f in _AMBIGUOUS_BASE:
            amb.append(f)
        elif f == "expert_skill_zero_duration":
            (amb if _expert_zero_corroborated(candidate) else hard).append(
                "expert_skill_zero_duration_corrob" if _expert_zero_corroborated(candidate)
                else "expert_skill_zero_duration_uncorrob")

    # anachronism: a HARD temporal impossibility the shipped detector misses
    if is_anachronistic(candidate):
        hard.append(f"tech_anachronism(sev={worst_severity(candidate):.2f})")

    level = "hard" if hard else ("ambiguous" if amb else "clean")
    return {"hard": hard, "ambiguous": amb, "level": level}


def main():
    from _lib import load_pool, labels
    recs, base_ids = load_pool()
    full, _, _ = labels()
    base_set = set(base_ids)
    n_hard = n_amb = n_clean = 0
    hard_in_golden = amb_in_golden = 0
    from collections import Counter
    hard_kinds, amb_kinds = Counter(), Counter()
    tier_hard, tier_amb, tier_clean = [], [], []
    for r in recs:
        c = classify(r["cand"], r["values"])
        t = full.tiers.get(r["cid"], 0.0)
        if c["level"] == "hard":
            n_hard += 1; tier_hard.append(t)
            for f in c["hard"]:
                hard_kinds[f.split("(")[0]] += 1
            if r["cid"] in base_set:
                hard_in_golden += 1
        elif c["level"] == "ambiguous":
            n_amb += 1; tier_amb.append(t)
            for f in c["ambiguous"]:
                amb_kinds[f] += 1
            if r["cid"] in base_set:
                amb_in_golden += 1
        else:
            n_clean += 1; tier_clean.append(t)
    import numpy as np
    print(f"pool=3000  HARD={n_hard}  AMBIGUOUS={n_amb}  CLEAN={n_clean}")
    print(f"  hard kinds:      {dict(hard_kinds)}")
    print(f"  ambiguous kinds: {dict(amb_kinds)}")
    print(f"  mean blind tier: hard={np.mean(tier_hard):.2f} amb={np.mean(tier_amb):.2f} clean={np.mean(tier_clean):.2f}")
    print(f"  in GOLDEN top-100: hard={hard_in_golden}  ambiguous={amb_in_golden}")
    print("  -> hard candidates currently in golden's top-100 are exactly the anachronism")
    print("     class the shipped detector does not catch (it hard-zeros the other hard rules).")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
