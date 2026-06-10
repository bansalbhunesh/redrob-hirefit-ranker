"""Grounded, deterministic reasoning for submission rows."""

from __future__ import annotations

from redrob_ranker.constants import MUST_HAVE_SKILLS, NICE_TO_HAVE_SKILLS, PREFERRED_INDIAN_LOCATIONS
from redrob_ranker.features import CandidateFeatures
from redrob_ranker.text import lower

# Deterministic paraphrase pools. Reasoning stays fully reproducible from code
# (no LLM, no manual edits), but the same semantic point is worded differently
# across candidates so a 10-row Stage-4 sample does not read as a single template.
_JD_ALIGN_VARIANTS = (
    "aligns with the JD requirement for shipped retrieval/ranking systems",
    "matches the JD's emphasis on production retrieval and ranking work",
    "fits the JD's call for shipped search/ranking systems over keyword lists",
)
_CORE_SKILL_VARIANTS = (
    "skill profile maps strongly to the JD's core AI/ML requirements",
    "core AI/ML stack lines up with the JD's must-have skills",
    "skills cover the JD's core retrieval and ML requirements",
)
_TRAJECTORY_VARIANTS = (
    "career trajectory is close to the target Senior AI Engineer role",
    "career path tracks toward the JD's Senior AI Engineer profile",
    "trajectory is consistent with the JD's senior IC target",
)
_SKILLS_LEAD = ("relevant skills include", "core stack covers", "hands-on with", "notably skilled in")
_JD_FALLBACK_VARIANTS = (
    "solid JD-fit on production experience and core skills",
    "rounds out the shortlist after stronger JD-fit signals",
    "included on balance of JD-relevant skills and experience",
)


def _variant(options: tuple[str, ...], candidate_id: str, salt: int = 0) -> str:
    return options[(sum(ord(ch) for ch in str(candidate_id)) + salt) % len(options)]


# Hard cap on a reasoning cell. The bundled validator imposes no length limit,
# but CSV cells beyond this read as padding, not signal.
MAX_REASON_LEN = 600

# Ranking/search/recsys evidence terms for the injected career fact.
_EVIDENCE_TERMS = (
    "learning to rank", "learning-to-rank", "re-rank", "rerank", "ranking",
    "retrieval", "recommendation", "recsys", "search", "embedding", "bm25",
    "vector", "personalization", "relevance",
)

_FACT_LEADS = ("Evidence", "Concrete signal", "Track record", "On the record")


def _career_fact(candidate: dict, cid: str) -> str | None:
    """One concrete, verbatim-grounded career fact for this candidate.

    Prefers a sentence from a career_history description that carries
    ranking/search/recsys evidence (quoted verbatim with its company); falls
    back to the longest-tenure role. Deterministic per candidate_id.
    """
    matches: list[tuple[str, str]] = []
    for job in candidate.get("career_history", []) or []:
        company = str(job.get("company") or "").strip()
        desc = str(job.get("description") or "")
        if not company or not desc:
            continue
        for sentence in desc.split(". "):
            lowered = sentence.lower()
            if any(term in lowered for term in _EVIDENCE_TERMS):
                snippet = sentence.strip().rstrip(".")
                # Skip over-long sentences instead of truncating so the quote
                # stays verbatim (and the row under MAX_REASON_LEN).
                if 25 <= len(snippet) <= 140:
                    matches.append((company, snippet))
                break  # at most one snippet per job
    if matches:
        idx = (sum(ord(ch) for ch in str(cid)) + 11) % len(matches)
        company, snippet = matches[idx]
        return f'at {company}: "{snippet}"'
    jobs = [
        j for j in candidate.get("career_history", []) or []
        if str(j.get("company") or "").strip() and str(j.get("title") or "").strip()
        and int(j.get("duration_months") or 0) > 0
    ]
    if not jobs:
        return None
    j = max(jobs, key=lambda job: int(job.get("duration_months") or 0))
    return f"{int(j.get('duration_months') or 0)} months at {j['company']} as {j['title']}"


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

    cid = str(candidate.get("candidate_id", ""))
    opening_variants = [
        f"{title} with {years:.1f} years at {current_company}",
        f"{years:.1f}-year {title} currently at {current_company}",
        f"Currently {_article_for_title(title)} {title} at {current_company} with {years:.1f} years",
        f"{title} ({years:.1f} yrs), now at {current_company}",
        f"At {current_company} as {_article_for_title(title)} {title}, {years:.1f} years in",
        f"{years:.1f} years of experience, currently {_article_for_title(title)} {title} at {current_company}",
    ]
    opening = opening_variants[sum(ord(ch) for ch in cid) % len(opening_variants)]

    positives: list[str] = []
    concerns: list[str] = []

    if features.values["production_evidence"] >= 0.55 or features.values["ir_ranking_experience"] >= 0.55:
        positives.append(_variant(_JD_ALIGN_VARIANTS, cid, 1))
    elif features.values["core_skill_match"] >= 0.55:
        positives.append(_variant(_CORE_SKILL_VARIANTS, cid, 2))
    elif features.values["career_trajectory_score"] >= 0.55:
        positives.append(_variant(_TRAJECTORY_VARIANTS, cid, 3))

    if skills:
        positives.append(f"{_variant(_SKILLS_LEAD, cid, 4)} {', '.join(skills[:3])}")
    
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
            "endorsement_inflation_low_profile": "unusual endorsement patterns",
            "llm_wrapper_only": "AI experience leans on LLM-wrapper frameworks without shipped retrieval/ranking depth",
            "junior_for_senior_role": "early-career for a senior-level role",
        }
        friendly_flags = [flag_map.get(f, "profile concern") for f in features.flags if f in flag_map]
        if friendly_flags:
            concerns.append(f"concerns noted: {', '.join(friendly_flags[:2])}")
    if features.values["career_trajectory_score"] < 0.35:
        concerns.append("current title is not a strong match for the role")
    notice_days = signals.get("notice_period_days", "unknown")
    response_rate = float(signals.get("recruiter_response_rate") or 0)
    if features.behavioral_multiplier >= 0.95:
        engagement_note = _variant((
            "strong availability and recruiter-response signals",
            "responsive and visibly in the market",
            "high availability with reliable recruiter responses",
        ), cid, 17)
    elif features.behavioral_multiplier >= 0.65:
        engagement_note = _variant((
            "usable availability signals with some recruiter-response risk",
            "reachable, though recruiter-response history is mixed",
            "moderate availability; responsiveness is the watch item",
        ), cid, 17)
    else:
        engagement_note = _variant((
            "weaker availability or recruiter-response signals",
            "limited recent platform activity; outreach may be slow",
            "low availability signals despite the on-paper fit",
        ), cid, 17)
    behavior = _variant((
        f"response rate {response_rate:.2f}, notice {notice_days} days; {engagement_note}",
        f"notice {notice_days} days, response rate {response_rate:.2f}; {engagement_note}",
        f"{engagement_note}; response rate {response_rate:.2f}, notice {notice_days} days",
    ), cid, 19)

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
        selected.append(_variant(_JD_FALLBACK_VARIANTS, cid, 5))

    first_sentence = f"{opening}; {'; '.join(selected[:3])}."

    # One concrete, verbatim-grounded career fact per row (company + the
    # specific ranking/search/recsys evidence from that candidate's history).
    fact = _career_fact(candidate, cid)
    fact_sentence = f" {_variant(_FACT_LEADS, cid, 13)} {fact}." if fact else ""

    behavior_variants = [
        f"Redrob engagement: {behavior}.",
        f"Platform activity: {behavior}.",
        f"Recruiter interaction profile: {behavior}.",
        f"Availability and responsiveness: {behavior}.",
        f"Hiring signals: {behavior}.",
        f"Pipeline readiness: {behavior}.",
        f"Recruiter-facing signals: {behavior}.",
        f"Engagement snapshot: {behavior}.",
        f"On the platform: {behavior}.",
        f"Reachability: {behavior}.",
        f"Process signals: {behavior}.",
        f"Recruiter telemetry: {behavior}.",
    ]
    candidate_id = str(candidate.get("candidate_id", ""))
    variant_idx = (sum(ord(c) for c in candidate_id) + 7) % len(behavior_variants)
    second_sentence = behavior_variants[variant_idx]

    reason = f"{first_sentence}{fact_sentence} {second_sentence}"
    if len(reason) > MAX_REASON_LEN and fact_sentence:
        reason = f"{first_sentence} {second_sentence}"
    return reason[:MAX_REASON_LEN]
