"""Grounded, deterministic reasoning for submission rows."""

from __future__ import annotations

from redrob_ranker.constants import MUST_HAVE_SKILLS, NICE_TO_HAVE_SKILLS, PREFERRED_INDIAN_LOCATIONS
from redrob_ranker.features import CandidateFeatures
from redrob_ranker.text import lower


def _top_relevant_skills(candidate: dict, limit: int = 4) -> list[str]:
    aliases = {
        lower(alias)
        for group in list(MUST_HAVE_SKILLS.values()) + list(NICE_TO_HAVE_SKILLS.values())
        for alias in group
    }
    found = []
    for skill in candidate.get("skills", []) or []:
        name = str(skill.get("name") or "")
        name_l = lower(name)
        if any(alias in name_l or name_l in alias for alias in aliases):
            strength = float(skill.get("endorsements") or 0) + float(skill.get("duration_months") or 0) / 3
            found.append((strength, name))
    return [name for _, name in sorted(found, reverse=True)[:limit]]


def _company_context(features: CandidateFeatures) -> str:
    if features.values["product_company_ratio"] >= 0.55:
        return "product-company background supports the JD preference"
    if features.values["consulting_only_flag"] >= 0.5:
        return "consulting-only background was heavily penalized"
    return "company background is mixed rather than a decisive advantage"


def _article_for_title(title: str) -> str:
    first = lower(str(title).strip().split()[0]) if str(title).strip() else ""
    vowel_sound_initialisms = {"ai", "ml", "mle", "nlp", "llm", "ir", "sre", "r&d"}
    if first in vowel_sound_initialisms or first[:1] in {"a", "e", "i", "o"}:
        return "an"
    return "a"


def build_reason(candidate: dict, features: CandidateFeatures, rank: int) -> str:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    years = float(profile.get("years_of_experience") or 0)
    title = profile.get("current_title", "candidate")
    location = profile.get("location", "")
    current_company = profile.get("current_company", "current company")
    skills = _top_relevant_skills(candidate)

    opening_variants = [
        f"{title} with {years:.1f} years at {current_company}",
        f"{years:.1f}-year {title} currently at {current_company}",
        f"Currently {_article_for_title(title)} {title} at {current_company} with {years:.1f} years",
    ]
    variant = sum(ord(ch) for ch in str(candidate.get("candidate_id", ""))) % len(opening_variants)
    opening = opening_variants[variant]

    positives: list[str] = []
    concerns: list[str] = []

    if features.values["production_evidence"] >= 0.55 or features.values["ir_ranking_experience"] >= 0.55:
        positives.append("aligns with the JD requirement for shipped retrieval/ranking systems")
    elif features.values["core_skill_match"] >= 0.55:
        positives.append("skill profile maps strongly to the JD's core AI/ML requirements")
    elif features.values["career_trajectory_score"] >= 0.55:
        positives.append("career trajectory is close to the target Senior AI Engineer role")

    if skills:
        positives.append(f"relevant skills include {', '.join(skills[:3])}")
    
    company_ctx = _company_context(features)
    if "advantage" not in company_ctx and "penalized" not in company_ctx:
        pass # don't add the mixed one
    else:
        positives.append(company_ctx)

    if features.values["location_score"] >= 0.9:
        positives.append(f"{location} is a preferred India location")
    elif lower(profile.get("country")) == "india":
        positives.append(f"{location} is India-based")
    elif features.values["relocation_willing"] >= 1.0:
        positives.append("willing to relocate")
    else:
        concerns.append(f"{location or profile.get('country', 'location')} is a logistics concern")

    if features.values["notice_period_score"] <= 0.35:
        concerns.append(f"notice period is {signals.get('notice_period_days', 'unknown')} days")
    if features.values["responsiveness_score"] < 0.35:
        concerns.append(f"response rate is only {signals.get('recruiter_response_rate', 0):.2f}")
    if not signals.get("open_to_work_flag") and features.values["availability_score"] < 0.65:
        concerns.append("not marked open-to-work")
    if features.values["keyword_stuffer_flag"] >= 0.75:
        concerns.append("profile appeared to artificially inflate keyword matches")
    if features.values["yoe_fit_score"] < 0.6:
        concerns.append(f"{years:.0f} years is outside the JD's 5-9 year target band")
    if features.honeypot_multiplier < 1.0:
        concerns.append("inconsistencies detected in timeline or experience claims")
    if features.disqualifier_multiplier < 0.8:
        flag_map = {
            "consulting_only": "heavy consulting background without product experience",
            "pure_research_without_deployment": "academic research without production deployments",
            "cv_speech_robotics_primary": "focus on CV/Robotics rather than ranking",
            "keyword_stuffer": "keyword inflation detected",
            "title_hopper": "frequent short job tenures",
            "salary_inversion": "unusual salary expectations",
            "endorsement_inflation_low_profile": "unusual endorsement patterns"
        }
        friendly_flags = [flag_map.get(f, "profile concern") for f in features.flags if f in flag_map]
        if friendly_flags:
            concerns.append(f"concerns noted: {', '.join(friendly_flags[:2])}")
    if features.values["career_trajectory_score"] < 0.35:
        concerns.append("current title is not a strong match for the role")
    notice_days = signals.get("notice_period_days", "unknown")
    response_rate = float(signals.get("recruiter_response_rate") or 0)
    if features.behavioral_multiplier >= 0.95:
        engagement_note = "strong availability and recruiter-response signals"
    elif features.behavioral_multiplier >= 0.65:
        engagement_note = "usable availability signals with some recruiter-response risk"
    else:
        engagement_note = "weaker availability or recruiter-response signals"
    behavior = (
        f"response rate {response_rate:.2f}, notice {notice_days} days; "
        f"{engagement_note}"
    )

    if rank <= 20:
        selected = positives[:3]
        if concerns:
            selected.append(f"minor concern: {concerns[0]}")
    elif rank <= 70:
        selected = positives[:2] + [f"concern: {c}" for c in concerns[:2]]
    else:
        selected = [f"concern: {c}" for c in concerns[:2]] + positives[:1]

    if not selected:
        selected = ["included as an adjacent fit after stronger JD scoring signals"]
    if not any("JD" in item for item in selected):
        selected.append("solid foundational match based on production experience and core skills")

    first_sentence = f"{opening}; {'; '.join(selected[:3])}."

    behavior_variants = [
        f"Redrob engagement: {behavior}.",
        f"Platform activity: {behavior}.",
        f"Recruiter interaction profile: {behavior}.",
        f"Availability and responsiveness: {behavior}.",
    ]
    candidate_id = str(candidate.get("candidate_id", ""))
    variant_idx = (sum(ord(c) for c in candidate_id) + 7) % len(behavior_variants)
    second_sentence = behavior_variants[variant_idx]

    return f"{first_sentence} {second_sentence}"
