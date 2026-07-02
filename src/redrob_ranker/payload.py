"""Shared dashboard payload rendering from grounded ranker features."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


HARD_HONEYPOT_FLAGS = {
    "experience_timeline_exceeds_claim",
    "career_history_too_short_for_claimed_yoe",
    "summary_career_yoe_contradiction",
    "expert_skill_zero_duration",
    "multiple_current_jobs",
    "impossible_education_timeline",
    "title_description_contradiction",
}


def _feature_data(features: Any) -> dict[str, Any]:
    if hasattr(features, "as_dict"):
        return dict(features.as_dict())
    if isinstance(features, Mapping):
        return dict(features)
    return {}


def _numeric_features(data: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    for key, val in data.items():
        if isinstance(val, bool):
            continue
        if isinstance(val, (int, float)):
            values[key] = round(float(val), 4)
    return values


def _flags(data: dict[str, Any]) -> list[str]:
    raw = data.get("flags", [])
    if isinstance(raw, str):
        return [flag.strip() for flag in raw.split(",") if flag.strip()]
    if isinstance(raw, (list, tuple, set)):
        return [str(flag).strip() for flag in raw if str(flag).strip()]
    return []


def _label_flag(flag: str) -> str:
    return flag.replace("_", " ").title()


def _tier(rank: int, honeypot_flag: bool) -> str:
    if honeypot_flag:
        return "honeypot"
    if rank == 1:
        return "gold"
    if rank == 2:
        return "silver"
    if rank == 3:
        return "bronze"
    return "standard"


def build_candidate_payload(
    candidate: dict,
    features: Any,
    raw_score: float,
    rank: int,
    reasoning: str,
    *,
    max_score: float | None = None,
) -> dict:
    """Build the UI/API payload using actual feature objects, never reasoning text."""
    prof = candidate.get("profile", {}) or {}
    redrob = candidate.get("redrob_signals", {}) or {}
    feature_data = _feature_data(features)
    feature_breakdown = _numeric_features(feature_data)
    flags = _flags(feature_data)

    honeypot_multiplier = float(feature_data.get("honeypot_multiplier", 1.0) or 0.0)
    behavioral_multiplier = float(feature_data.get("behavioral_multiplier", 1.0) or 0.0)
    disqualifier_multiplier = float(feature_data.get("disqualifier_multiplier", 1.0) or 0.0)
    hard_flags = [flag for flag in flags if flag in HARD_HONEYPOT_FLAGS]
    honeypot_flag = honeypot_multiplier <= 0.0 or bool(hard_flags)
    honeypot_reasons = [_label_flag(flag) for flag in hard_flags]
    if honeypot_flag and not honeypot_reasons:
        honeypot_reasons = ["Hard Honeypot Guardrail"]

    normalized_score = raw_score / max_score if max_score and max_score > 0 else raw_score
    normalized_score = max(0.0, min(1.0, float(normalized_score)))

    timeline = [
        {
            "company": job.get("company", "Unknown"),
            "title": job.get("title", "Unknown"),
            "start": job.get("start_date", ""),
            "end": job.get("end_date", "Present"),
            "duration_months": job.get("duration_months", 0),
            "is_current": job.get("is_current", False),
            "industry": job.get("industry", "Unknown"),
            "company_size": job.get("company_size", "Unknown"),
        }
        for job in (candidate.get("career_history", []) or [])
    ]

    skills_cloud = [
        {
            "name": skill.get("name", "Unknown"),
            "proficiency": skill.get("proficiency", "unknown"),
            "endorsements": skill.get("endorsements", 0),
            "duration_months": skill.get("duration_months", 0),
        }
        for skill in (candidate.get("skills", []) or [])
    ]

    edu_list = [
        {
            "institution": edu.get("institution", "Unknown"),
            "degree": edu.get("degree", "Unknown"),
            "field": edu.get("field_of_study", "Unknown"),
            "start": edu.get("start_year", ""),
            "end": edu.get("end_year", ""),
            "grade": edu.get("grade", ""),
            "tier": edu.get("tier", "unknown"),
        }
        for edu in (candidate.get("education", []) or [])
    ]

    behavioral = {
        "profile_completeness": redrob.get("profile_completeness_score", 0),
        "open_to_work": redrob.get("open_to_work_flag", False),
        "response_rate": redrob.get("recruiter_response_rate", 0),
        "avg_response_time": redrob.get("avg_response_time_hours", 0),
        "interview_completion": redrob.get("interview_completion_rate", 0),
        "offer_acceptance": redrob.get("offer_acceptance_rate", 0),
        "github_activity": redrob.get("github_activity_score", 0),
        "saved_by_recruiters": redrob.get("saved_by_recruiters_30d", 0),
        "profile_views": redrob.get("profile_views_received_30d", 0),
        "notice_period": redrob.get("notice_period_days", 0),
        "verified_email": redrob.get("verified_email", False),
        "verified_phone": redrob.get("verified_phone", False),
        "skill_assessments": redrob.get("skill_assessment_scores", {}),
        "connection_count": redrob.get("connection_count", 0),
        "endorsements": redrob.get("endorsements_received", 0),
        "expected_salary": redrob.get("expected_salary_range_inr_lpa", {}),
        "preferred_work_mode": redrob.get("preferred_work_mode", "unknown"),
        "willing_to_relocate": redrob.get("willing_to_relocate", False),
    }

    return {
        "candidate_id": candidate.get("candidate_id", "Unknown"),
        "rank": rank,
        "score": round(normalized_score, 4),
        "raw_score": round(float(raw_score), 6),
        "tier": _tier(rank, honeypot_flag),
        "honeypot_flag": honeypot_flag,
        "honeypot_reasons": honeypot_reasons,
        "flags": flags,
        "multipliers": {
            "behavioral": round(behavioral_multiplier, 4),
            "honeypot": round(honeypot_multiplier, 4),
            "disqualifier": round(disqualifier_multiplier, 4),
        },
        "reasoning": reasoning,
        "features": feature_breakdown,
        "behavioral": behavioral,
        "profile": {
            "name": prof.get("anonymized_name", "Unknown"),
            "headline": prof.get("headline", ""),
            "summary": prof.get("summary", ""),
            "title": prof.get("current_title", "Unknown"),
            "company": prof.get("current_company", "Unknown"),
            "company_size": prof.get("current_company_size", "Unknown"),
            "industry": prof.get("current_industry", "Unknown"),
            "location": prof.get("location", "Unknown"),
            "country": prof.get("country", "Unknown"),
            "yoe": float(prof.get("years_of_experience", 0.0) or 0.0),
        },
        "timeline": timeline,
        "skills": skills_cloud,
        "education": edu_list,
        "certifications": [cert.get("name", "Unknown") for cert in (candidate.get("certifications", []) or [])],
        "languages": [
            {"language": lang.get("language", ""), "proficiency": lang.get("proficiency", "")}
            for lang in (candidate.get("languages", []) or [])
        ],
    }
