"""Plan D v2 deterministic feature extraction and multiplicative scoring."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date

from redrob_ranker.constants import (
    BASE_FEATURE_WEIGHTS,
    CODE_WRITING_SIGNALS,
    CV_SPEECH_ROBOTICS_TERMS,
    FEATURE_NAMES,
    IR_RANKING_SIGNALS,
    MUST_HAVE_SKILLS,
    MUST_HAVE_WEIGHTS,
    NICE_TO_HAVE_SKILLS,
    NON_TARGET_TITLES,
    OPEN_SOURCE_SIGNALS,
    PREFERRED_INDIAN_LOCATIONS,
    PRODUCT_COMPANIES,
    PRODUCT_INDUSTRIES,
    PRODUCTION_SIGNALS,
    PURE_RESEARCH_SIGNALS,
    SCALE_SIGNALS,
    SERVICES_COMPANIES,
    TARGET_TITLE_WEIGHTS,
)
from redrob_ranker.text import candidate_text, lower

REFERENCE_DATE = date(2026, 6, 8)

_NORM_RE = re.compile(r"[^a-z0-9+#.\s/-]")
BOUNDARY_MATCH_TERMS = {
    "ai",
    "ml",
    "ann",
    "api",
    "map",
    "rag",
    "mrr",
    "tts",
    "gan",
    "gans",
    "live",
    "daily",
    "paper",
    "talk",
    "scale",
    "recall",
    "search",
    "service",
}


@dataclass(slots=True)
class CandidateFeatures:
    candidate_id: str
    values: dict[str, float]
    behavioral_multiplier: float
    honeypot_multiplier: float
    disqualifier_multiplier: float
    flags: list[str] = field(default_factory=list)
    total: float = 0.0

    def as_dict(self) -> dict[str, float | str]:
        data: dict[str, float | str] = {"candidate_id": self.candidate_id, **self.values}
        data["behavioral_multiplier"] = self.behavioral_multiplier
        data["honeypot_multiplier"] = self.honeypot_multiplier
        data["disqualifier_multiplier"] = self.disqualifier_multiplier
        data["flags"] = ",".join(self.flags)
        data["total"] = self.total
        return data

    # Compatibility/convenience properties used by reasoning and tests.
    @property
    def role_fit(self) -> float:
        return clamp(
            0.45 * self.values["career_trajectory_score"]
            + 0.30 * self.values["senior_title_held"]
            + 0.25 * self.values["yoe_fit_score"]
        )

    @property
    def ai_depth(self) -> float:
        return clamp(
            0.50 * self.values["core_skill_match"]
            + 0.25 * self.values["nice_skill_match"]
            + 0.25 * self.values["skill_depth_score"]
        )

    @property
    def production_evidence(self) -> float:
        return self.values["production_evidence"]

    @property
    def product_company(self) -> float:
        return self.values["product_company_ratio"]

    @property
    def behavior(self) -> float:
        return clamp((self.behavioral_multiplier - 0.25) / 1.25)

    @property
    def logistics(self) -> float:
        return clamp(0.75 * self.values["location_score"] + 0.25 * self.values["notice_period_score"])

    @property
    def honeypot_risk(self) -> float:
        return 1.0 - self.honeypot_multiplier

    @property
    def keyword_stuffing_risk(self) -> float:
        return self.values["keyword_stuffer_flag"]

    @property
    def negative_penalty(self) -> float:
        return 1.0 - self.disqualifier_multiplier


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
_NORM_RE = re.compile(r"[^a-z0-9+#\s]")

def _norm(text: object) -> str:
    return _NORM_RE.sub(" ", str(text or "").lower()).strip()


def _pad(terms):
    padded = []
    for t in terms:
        t_clean = t.strip().replace('.', ' ').replace('/', ' ').replace('-', ' ')
        padded.append(f" {t_clean} ")
    return padded

def _has_boundary(padded_terms, text: str) -> bool:
    safe_text = f" {text} "
    for pt in padded_terms:
        if pt in safe_text:
            return True
    return False

def _count_boundaries(padded_terms, text: str) -> int:
    safe_text = f" {text} "
    count = 0
    for pt in padded_terms:
        if pt in safe_text:
            count += 1
    return count

def _contains_padded(padded_terms: list[str], text: str) -> int:
    return _count_boundaries(padded_terms, text)

def _contains(text: str, terms: set[str] | list[str]) -> int:
    return _contains_padded(_pad([str(t).lower() for t in terms]), text)


NORMALIZED_MUST_HAVE_SKILLS = {
    group: tuple(_norm(alias) for alias in aliases) for group, aliases in MUST_HAVE_SKILLS.items()
}
NORMALIZED_NICE_TO_HAVE_SKILLS = {
    group: tuple(_norm(alias) for alias in aliases) for group, aliases in NICE_TO_HAVE_SKILLS.items()
}


def _days_since(date_s: str | None) -> int:
    if not date_s:
        return 9999
    try:
        y, m, d = [int(x) for x in date_s[:10].split("-")]
        return max(0, (REFERENCE_DATE - date(y, m, d)).days)
    except Exception:
        return 9999


def _skill_records(candidate: dict) -> list[dict]:
    return candidate.get("skills", []) or []


def _skill_terms(candidate: dict) -> set[str]:
    terms: set[str] = set()
    for skill in _skill_records(candidate):
        name = _norm(skill.get("name"))
        if not name:
            continue
        terms.add(name)
        for token in name.split():
            if len(token) > 2:
                terms.add(token)
    return terms


def skill_names(candidate: dict) -> list[str]:
    return [_norm(s.get("name")) for s in _skill_records(candidate)]


def _profile_text(candidate: dict) -> str:
    # Reuse cached text from retrieve_pool if available, else compute fresh.
    cached = candidate.get("_cached_text")
    if cached is not None:
        return _norm(cached)
    return _norm(candidate_text(candidate))


def _career_text(candidate: dict) -> str:
    parts = [candidate.get("profile", {}).get("summary", "")]
    for job in candidate.get("career_history", []) or []:
        parts.extend([job.get("title", ""), job.get("description", ""), job.get("industry", "")])
    return _norm(" ".join(parts))


def _alias_match(candidate_terms: set[str], full_text: str, full_tokens: set[str], aliases: list[str]) -> float:
    score = 0.0
    for alias_n in aliases:
        if alias_n in candidate_terms:
            score = max(score, 1.0)
        elif _has_boundary(_pad([alias_n]), full_text):
            score = max(score, 0.7)
    return score


_TARGET_TITLE_PADDED = {f" {t.strip().replace('.', ' ').replace('/', ' ').replace('-', ' ')} ": w for t, w in TARGET_TITLE_WEIGHTS.items()}
_NON_TARGET_PADDED = _pad(NON_TARGET_TITLES)

def _title_score(candidate: dict) -> float:
    profile = candidate.get("profile", {})
    current = _norm(profile.get("current_title"))
    headline = _norm(profile.get("headline"))
    historical = " ".join(_norm(j.get("title")) for j in candidate.get("career_history", []) or [])
    text = f"{current} {headline} {historical}"

    score = 0.08
    safe_text = f" {text} "
    for pt, weight in _TARGET_TITLE_PADDED.items():
        if pt in safe_text:
            score = max(score, weight)
    if _has_boundary(_NON_TARGET_PADDED, current):
        score = min(score, 0.18)
    return clamp(score)


_SERVICES_PADDED = _pad(SERVICES_COMPANIES)

def _is_consulting(company: str) -> bool:
    name = _norm(company)
    return _has_boundary(_SERVICES_PADDED, name)


_PRODUCT_COMPANIES_PADDED = _pad(PRODUCT_COMPANIES)
_PRODUCT_INDUSTRIES_PADDED = _pad(PRODUCT_INDUSTRIES)
_TECH_INDUSTRIES_PADDED = _pad(["software", "tech", "data", "platform"])

def _is_product_job(job: dict) -> bool:
    company = _norm(job.get("company"))
    industry = _norm(job.get("industry"))
    size = str(job.get("company_size") or "")
    if _has_boundary(_PRODUCT_COMPANIES_PADDED, company):
        return True
    if _is_consulting(company):
        return False
    if _has_boundary(_PRODUCT_INDUSTRIES_PADDED, industry):
        return True
    return size in {"51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"} and _has_boundary(
        _TECH_INDUSTRIES_PADDED, industry
    )


def _product_consulting_months(candidate: dict) -> tuple[int, int, int]:
    total = product = consulting = 0
    for job in candidate.get("career_history", []) or []:
        months = int(job.get("duration_months") or 0)
        total += months
        if _is_product_job(job):
            product += months
        if _is_consulting(str(job.get("company") or "")):
            consulting += months
    return product, consulting, total


_EDU_FIELDS_PADDED = _pad(["computer", "artificial intelligence", "data science", "statistics", "mathematics", "information technology"])
_EDU_DEGREES_PADDED = _pad(["m.tech", "m.e", "m.s", "m.sc", "ph.d", "phd"])

def _education_score(candidate: dict) -> float:
    best = 0.0
    tier_scores = {"tier_1": 1.0, "tier_2": 0.8}
    for edu in candidate.get("education", []) or []:
        score = tier_scores.get(str(edu.get("tier") or "unknown"), 0.5)
        field = _norm(edu.get("field_of_study"))
        degree = _norm(edu.get("degree"))
        if _has_boundary(_EDU_FIELDS_PADDED, field):
            score += 0.12
        if _has_boundary(_EDU_DEGREES_PADDED, degree):
            score += 0.05
        best = max(best, clamp(score))
    return best or 0.45


def _honeypot_flags(candidate: dict, values: dict[str, float]) -> list[str]:
    _CORE_ALIASES_PADDED = _pad([a for g in NORMALIZED_MUST_HAVE_SKILLS.values() for a in g] + [a for g in NORMALIZED_NICE_TO_HAVE_SKILLS.values() for a in g])
    flags: list[str] = []
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", []) or []
    skills = _skill_records(candidate)

    yoe = float(profile.get("years_of_experience") or 0)
    expected_months = int(yoe * 12)
    career_months = sum(int(j.get("duration_months") or 0) for j in career)
    if expected_months and career_months > expected_months + 30:
        flags.append("experience_timeline_exceeds_claim")
    if yoe >= 5 and career and career_months < expected_months * 0.45:
        flags.append("career_history_too_short_for_claimed_yoe")

    expert_zero_core = []
    expert_zero_any = []
    for skill in candidate.get("skills", []) or []:
        if str(skill.get("proficiency") or "").lower() != "expert" or int(skill.get("duration_months") or 0) != 0:
            continue
        expert_zero_any.append(skill.get("name", ""))
        name_n = _norm(skill.get("name"))
        if _has_boundary(_CORE_ALIASES_PADDED, name_n):
            expert_zero_core.append(skill.get("name", ""))
    if len(expert_zero_core) >= 2 or len(expert_zero_any) >= 5:
        flags.append("expert_skill_zero_duration")

    if sum(1 for j in career if j.get("is_current")) > 2:
        flags.append("multiple_current_jobs")

    for edu in candidate.get("education", []) or []:
        start = int(edu.get("start_year") or 0)
        end = int(edu.get("end_year") or 0)
        if start and end and (end < start or start < 1970 or end > 2035):
            flags.append("impossible_education_timeline")
            break

    title = _norm(profile.get("current_title"))
    if _has_boundary(NON_TARGET_TITLES, title) and values["ir_ranking_experience"] >= 0.45:
        flags.append("title_description_contradiction")

    return flags


_SENIOR_TITLES_PADDED = _pad(["senior", "staff", "lead", "principal"])
_IR_RANKING_PADDED = _pad([str(t).lower() for t in IR_RANKING_SIGNALS])
_OPEN_SOURCE_PADDED = _pad([str(t).lower() for t in OPEN_SOURCE_SIGNALS])
_MANAGEMENT_PADDED = _pad(["manager", "lead", "head", "vp", "director"])

def compute_features(candidate: dict) -> CandidateFeatures:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    full_text = _profile_text(candidate)
    career_text = _career_text(candidate)
    full_tokens = set(full_text.split())
    terms = _skill_terms(candidate)
    values: dict[str, float] = {}

    core_score = 0.0
    for group, aliases in NORMALIZED_MUST_HAVE_SKILLS.items():
        core_score += MUST_HAVE_WEIGHTS[group] * _alias_match(terms, full_text, full_tokens, aliases)
    values["core_skill_match"] = clamp(core_score)

    nice_hits = [
        _alias_match(terms, full_text, full_tokens, aliases)
        for aliases in NORMALIZED_NICE_TO_HAVE_SKILLS.values()
    ]
    values["nice_skill_match"] = clamp(sum(nice_hits) / max(1, len(nice_hits)))

    matched_skill_scores = []
    
    for skill in _skill_records(candidate):
        name = _norm(skill.get("name"))
        if not name:
            continue
        prof = {"beginner": 0.35, "intermediate": 0.6, "advanced": 0.85, "expert": 1.0}.get(
            _norm(skill.get("proficiency")), 0.4
        )
        duration = clamp(float(skill.get("duration_months") or 0) / 36.0)
        endorsements = clamp(math.log1p(float(skill.get("endorsements") or 0)) / math.log1p(60))
        matched_skill_scores.append(0.45 * prof + 0.35 * duration + 0.20 * endorsements)
    values["skill_depth_score"] = clamp(sum(matched_skill_scores) / max(1, min(7, len(matched_skill_scores))))

    if _skill_records(candidate):
        credibility = []
        for skill in _skill_records(candidate):
            endorsements = float(skill.get("endorsements") or 0)
            duration = float(skill.get("duration_months") or 0)
            penalty = 0.55 if endorsements > 30 and duration < 6 else 1.0
            credibility.append(clamp((math.log1p(endorsements) / math.log1p(60)) * penalty))
        values["endorsement_trust"] = clamp(sum(credibility) / len(credibility))

    assessments = signals.get("skill_assessment_scores", {}) or {}
    if assessments:
        values["assessment_score_avg"] = clamp(sum(float(v) for v in assessments.values()) / (100 * len(assessments)))

    gh = float(signals.get("github_activity_score") or 0)
    values["github_signal"] = 0.0 if gh < 0 else clamp(gh / 100.0)

    cv_count = _contains(full_text, CV_SPEECH_ROBOTICS_TERMS)

    product_months, consulting_months, total_months = _product_consulting_months(candidate)
    values["product_company_ratio"] = clamp(product_months / max(1, total_months))
    values["consulting_only_flag"] = 1.0 if total_months and consulting_months / total_months > 0.8 and values["product_company_ratio"] < 0.2 else 0.0

    values["ir_ranking_experience"] = clamp(_contains(career_text, IR_RANKING_SIGNALS) / 7.0)
    values["production_evidence"] = clamp(_contains(career_text, PRODUCTION_SIGNALS) / 8.0)
    if sum(1 for j in candidate.get("career_history", []) or [] if int(j.get("duration_months") or 0) >= 18) >= 2:
        values["production_evidence"] = clamp(values["production_evidence"] + 0.08)

    title_text = " ".join(_norm(j.get("title")) for j in candidate.get("career_history", []) or [])
    current_title = _norm(profile.get("current_title"))
    values["senior_title_held"] = 1.0 if _has_boundary(_SENIOR_TITLES_PADDED, f"{current_title} {title_text}") and _title_score(candidate) > 0.55 else 0.0

    title_score = _title_score(candidate)
    short_jobs = sum(1 for j in candidate.get("career_history", []) or [] if int(j.get("duration_months") or 0) < 9)
    title_hop_penalty = 0.35 if short_jobs >= 3 else 0.0
    values["career_trajectory_score"] = clamp(0.75 * title_score + 0.25 * values["product_company_ratio"] - title_hop_penalty)
    values["scale_signal"] = clamp(_contains(career_text, SCALE_SIGNALS) / 4.0)
    values["code_writing_recent"] = clamp(_contains(" ".join([current_title, career_text]), CODE_WRITING_SIGNALS) / 4.0)

    yoe = float(profile.get("years_of_experience") or 0)
    values["yoe_fit_score"] = 1.0 if yoe >= 7.0 else clamp(math.exp(-((yoe - 7.0) ** 2) / (2 * 2.6**2)))
    if yoe < 3:
        values["yoe_fit_score"] *= 0.55
    values["education_score"] = _education_score(candidate)

    ml_months = 0
    _ML_TERMS_PADDED = _pad(["machine learning", " ai ", " ml ", "nlp", "data science"])
    for job in candidate.get("career_history", []) or []:
        text = _norm(" ".join([str(job.get("title", "")), str(job.get("description", ""))]))
        if _contains_padded(_IR_RANKING_PADDED, text) or _has_boundary(_ML_TERMS_PADDED, text):
            ml_months += int(job.get("duration_months") or 0)
    values["ml_ai_tenure_score"] = clamp(ml_months / 60.0)
    values["open_source_signal"] = clamp(_contains_padded(_OPEN_SOURCE_PADDED, full_text) / 3.0)

    management_score = _contains_padded(_MANAGEMENT_PADDED, career_text)
    last_active_days = _days_since(signals.get("last_active_date"))
    recency = 1.0 if last_active_days <= 14 else 0.9 if last_active_days <= 30 else 0.72 if last_active_days <= 60 else 0.5 if last_active_days <= 120 else 0.22
    values["availability_score"] = clamp(recency * (1.0 if signals.get("open_to_work_flag") else 0.68))

    views = float(signals.get("profile_views_received_30d") or 0)
    apps = float(signals.get("applications_submitted_30d") or 0)
    saved = float(signals.get("saved_by_recruiters_30d") or 0)
    search = float(signals.get("search_appearance_30d") or 0)
    values["engagement_score"] = clamp(0.25 * views / 80 + 0.20 * apps / 12 + 0.35 * saved / 12 + 0.20 * search / 250)

    rr = clamp(float(signals.get("recruiter_response_rate") or 0))
    response_time = float(signals.get("avg_response_time_hours") or 999)
    time_score = 1.0 if response_time <= 12 else 0.85 if response_time <= 24 else 0.65 if response_time <= 72 else 0.35 if response_time <= 168 else 0.15
    values["responsiveness_score"] = clamp(0.75 * rr + 0.25 * time_score)
    values["interview_reliability"] = clamp(float(signals.get("interview_completion_rate") or 0))

    completeness = clamp(float(signals.get("profile_completeness_score") or 0) / 100.0)
    verified = (
        (0.45 if signals.get("verified_email") else 0.0)
        + (0.35 if signals.get("verified_phone") else 0.0)
        + (0.20 if signals.get("linkedin_connected") else 0.0)
    )
    values["profile_quality"] = clamp(0.70 * completeness + 0.30 * verified)

    notice = float(signals.get("notice_period_days") or 180)
    values["notice_period_score"] = 1.0 if notice <= 30 else 0.93 if notice <= 60 else 0.85 if notice <= 90 else 0.45 if notice <= 120 else 0.20

    location = _norm(profile.get("location"))
    country = _norm(profile.get("country"))
    _LOCATIONS_PADDED = _pad(PREFERRED_INDIAN_LOCATIONS)
    preferred_city = _has_boundary(_LOCATIONS_PADDED, location)
    in_india = country == "india" or "india" in country
    willing_relocate = bool(signals.get("willing_to_relocate"))
    values["location_score"] = 1.0 if preferred_city else 0.68 if in_india else 0.42 if willing_relocate else 0.10
    values["relocation_willing"] = 1.0 if willing_relocate else 0.0

    non_target_title = _has_boundary(NON_TARGET_TITLES, current_title)
    skill_count = len(_skill_records(candidate))
    values["keyword_stuffer_flag"] = 1.0 if (
        skill_count >= 14
        and values["core_skill_match"] >= 0.45
        and values["production_evidence"] < 0.25
        and (non_target_title or values["career_trajectory_score"] < 0.35)
    ) else 0.0

    values["disqualifier_skill_flag"] = 1.0 if (
        cv_count >= 3 and values["ir_ranking_experience"] < 0.3
    ) else 0.0

    hard_flags = _honeypot_flags(candidate, values)
    soft_flags: list[str] = []
    if values["consulting_only_flag"]:
        soft_flags.append("consulting_only")
    salary = signals.get("expected_salary_range_inr_lpa", {}) or {}
    if float(salary.get("min") or 0) > float(salary.get("max") or 0) > 0:
        soft_flags.append("salary_inversion")
    if float(signals.get("profile_completeness_score") or 0) < 40 and int(signals.get("endorsements_received") or 0) > 40:
        soft_flags.append("endorsement_inflation_low_profile")
    if _contains(career_text, PURE_RESEARCH_SIGNALS) and values["production_evidence"] < 0.35:
        soft_flags.append("pure_research_without_deployment")
    if values["disqualifier_skill_flag"]:
        soft_flags.append("cv_speech_robotics_primary")
    if values["keyword_stuffer_flag"]:
        soft_flags.append("keyword_stuffer")
    if short_jobs >= 4:
        soft_flags.append("title_hopper")

    behavioral_multiplier = compute_behavioral_multiplier(values, candidate)
    honeypot_multiplier = 0.0 if hard_flags else 1.0
    disqualifier_multiplier = compute_disqualifier_multiplier(
        soft_flags, production_evidence=values["production_evidence"]
    )

    return CandidateFeatures(
        candidate_id=candidate["candidate_id"],
        values={k: clamp(v) for k, v in values.items()},
        behavioral_multiplier=behavioral_multiplier,
        honeypot_multiplier=honeypot_multiplier,
        disqualifier_multiplier=disqualifier_multiplier,
        flags=hard_flags + soft_flags,
    )


def compute_behavioral_multiplier(values: dict[str, float], candidate: dict) -> float:
    signals = candidate.get("redrob_signals", {})
    mult = 1.0
    mult *= 1.15 if signals.get("open_to_work_flag") else 0.95
    mult *= 0.5 + 0.5 * math.sqrt(values["responsiveness_score"])
    mult *= 0.7 + 0.3 * values["profile_quality"]
    mult *= 0.85 + 0.25 * values["availability_score"]
    mult *= 0.8 + 0.2 * values["interview_reliability"]
    mult *= 1.05 if float(signals.get("saved_by_recruiters_30d") or 0) > 5 else 0.95 if float(signals.get("saved_by_recruiters_30d") or 0) == 0 else 1.0
    raw_github = float(signals.get("github_activity_score") or 0)
    mult *= 1.05 if values["github_signal"] > 0.2 else 1.0
    if candidate.get("redrob_signals", {}).get("skill_assessment_scores"):
        mult *= 1.05 if values["assessment_score_avg"] > 0.6 else 0.9 if values["assessment_score_avg"] < 0.4 else 1.0
        mult *= _assessment_claim_multiplier(candidate)
    offer_rate = signals.get("offer_acceptance_rate")
    if offer_rate is not None and float(offer_rate) >= 0:
        mult *= 0.85 + 0.30 * clamp(float(offer_rate))
    mult *= 1.02 if values["profile_quality"] > 0.82 else 1.0
    mult *= 1.05 if values["notice_period_score"] >= 1.0 else 0.70 if values["notice_period_score"] <= 0.2 else 1.0
    return clamp(mult, 0.25, 1.5)


def _assessment_claim_multiplier(candidate: dict) -> float:
    assessments = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {}) or {}
    if not assessments:
        return 1.0

    assessment_lookup = {_norm(k): float(v) for k, v in assessments.items()}
    multiplier = 1.0
    expected_by_proficiency = {
        "beginner": 30.0,
        "intermediate": 50.0,
        "advanced": 70.0,
        "expert": 85.0,
    }
    for skill in _skill_records(candidate):
        name = _norm(skill.get("name"))
        assessed = assessment_lookup.get(name)
        if assessed is None:
            continue
        expected = expected_by_proficiency.get(_norm(skill.get("proficiency")))
        if expected is not None and assessed < expected - 20:
            multiplier *= 0.86
    return clamp(multiplier, 0.55, 1.0)


def compute_disqualifier_multiplier(flags: list[str], production_evidence: float = 0.0) -> float:
    mult = 1.0
    if "consulting_only" in flags:
        mult *= 0.80 if production_evidence > 0.5 else 0.35
    if "pure_research_without_deployment" in flags:
        mult *= 0.45
    if "cv_speech_robotics_primary" in flags:
        mult *= 0.60
    if "keyword_stuffer" in flags:
        mult *= 0.70
    if "title_hopper" in flags:
        mult *= 0.75
    if "salary_inversion" in flags:
        mult *= 0.65
    if "endorsement_inflation_low_profile" in flags:
        mult *= 0.70
    return clamp(mult, 0.05, 1.0)


def final_score(features: CandidateFeatures, retrieval_score: float = 0.0) -> float:
    weighted_sum = BASE_FEATURE_WEIGHTS["bm25_score"] * clamp(retrieval_score)
    total_weight = BASE_FEATURE_WEIGHTS["bm25_score"]
    for name, weight in BASE_FEATURE_WEIGHTS.items():
        if name == "bm25_score":
            continue
        weighted_sum += weight * features.values.get(name, 0.0)
        total_weight += weight
    base_score = weighted_sum / total_weight
    return max(
        0.0,
        base_score
        * features.behavioral_multiplier
        * features.honeypot_multiplier
        * features.disqualifier_multiplier,
    )
