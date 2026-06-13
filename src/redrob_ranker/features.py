"""Plan D v2 deterministic feature extraction and multiplicative scoring."""

from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
import os

from redrob_ranker.constants import (
    BASE_FEATURE_WEIGHTS,
    CODE_WRITING_SIGNALS,
    CV_SPEECH_ROBOTICS_TERMS,
    FEATURE_NAMES,
    IR_RANKING_SIGNALS,
    LLM_WRAPPER_TERMS,
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

# Pinned to the hackathon dataset timeframe by default to ensure reproducibility.
# Can be overridden for live production via REDROB_REFERENCE_DATE.
_env_date = os.environ.get("REDROB_REFERENCE_DATE")
REFERENCE_DATE = date.fromisoformat(_env_date) if _env_date else date(2026, 6, 8)

_NORM_RE = re.compile(r"[^a-z0-9+#\s]")


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


def _norm_str(text: str) -> str:
    return _NORM_RE.sub(" ", text.lower()).strip()


@lru_cache(maxsize=1 << 16)
def _norm_cached(text: str) -> str:
    return _norm_str(text)


def _norm(text: object) -> str:
    s = str(text or "")
    # Short strings (titles, companies, skills, proficiencies) repeat heavily
    # across the 100K pool -- caching them removes most re.sub calls from the
    # hot path. Long texts are unique per candidate, so caching would only
    # bloat memory.
    if len(s) <= 80:
        return _norm_cached(s)
    return _norm_str(s)


def _pad(terms) -> tuple[str, ...]:
    padded: list[str] = []
    for t in terms:
        t_clean = _norm(str(t).replace(".", " ").replace("/", " ").replace("-", " "))
        if t_clean:
            padded.append(f" {t_clean} ")
    return tuple(padded)


def _has_boundary_safe(padded_terms, safe_text: str) -> bool:
    """Boundary check against an already-padded (' text ') string."""
    for pt in padded_terms:
        if pt in safe_text:
            return True
    return False


def _has_boundary(padded_terms, text: str) -> bool:
    return _has_boundary_safe(padded_terms, f" {text} ")


def _count_in_safe(padded_terms, safe_text: str) -> int:
    """Boundary count against an already-padded (' text ') string.

    Padding once per candidate (instead of per term-list call) avoids
    re-copying the full profile text 10+ times per candidate; this is the
    compute_features hot path identified by cProfile.
    """
    count = 0
    for pt in padded_terms:
        if pt in safe_text:
            count += 1
    return count


def _count_boundaries(padded_terms, text: str) -> int:
    return _count_in_safe(padded_terms, f" {text} ")


def _contains_padded(padded_terms: tuple[str, ...], text: str) -> int:
    return _count_boundaries(padded_terms, text)


def _contains(text: str, terms: set[str] | list[str]) -> int:
    return _contains_padded(_pad(terms), text)


def _split_padded(padded_terms) -> tuple[frozenset[str], tuple[tuple[str, tuple[str, ...]], ...]]:
    """Split padded terms into (single-word set, multi-word (padded, words) tuple).

    For _norm()-ed text (single-space separated), a padded single-word term
    ' x ' is a substring of ' text ' exactly when x is a whitespace token of
    the text — so single-word checks can use a per-candidate token set
    instead of scanning the multi-KB string. Multi-word terms keep the
    substring check (they must match consecutive tokens), but carry their
    word tuple so callers can prune with token-set lookups first: if
    ' a b ' is a substring of the space-padded text, then 'a' and 'b' are
    each delimited by literal spaces there, hence members of the
    split(" ") token set. Words are only recorded when the term's internal
    whitespace is literal spaces (always true for _pad output); otherwise
    the empty tuple disables pruning and the substring scan always runs.
    """
    singles: set[str] = set()
    multis: list[tuple[str, tuple[str, ...]]] = []
    for pt in padded_terms:
        word = pt.strip()
        if " " in word:
            space_words = [w for w in word.split(" ") if w]
            words = tuple(space_words) if space_words == word.split() else ()
            multis.append((pt, words))
        else:
            singles.add(word)
    return frozenset(singles), tuple(multis)


def _count_tokenized(split_terms, token_set: set[str], safe_text: str) -> int:
    """Equivalent of _count_in_safe using a prebuilt token set for singles."""
    singles, multis = split_terms
    count = len(singles & token_set)
    for pt, words in multis:
        for w in words:
            if w not in token_set:
                break
        else:
            if pt in safe_text:
                count += 1
    return count


def _has_tokenized(split_terms, token_set: set[str], safe_text: str) -> bool:
    singles, multis = split_terms
    if singles & token_set:
        return True
    for pt, words in multis:
        for w in words:
            if w not in token_set:
                break
        else:
            if pt in safe_text:
                return True
    return False


class JDMatchers:
    """All JD-derived matching structures, prebuilt from a CompiledJD.

    The default instance reproduces the historical module-level constants
    exactly; alternate JDs (rank.py --jd) get their own instance. Scoring
    logic never changes -- only which compiled tables it matches against.
    """

    __slots__ = (
        "jd", "weights", "normalized_must", "normalized_nice",
        "padded_must", "padded_nice", "split_must", "split_nice",
        "relevant_padded", "split_relevant", "core_padded",
        "title_padded", "locations_padded", "yoe_target",
        "_relevant_name_cache",
    )

    def __init__(self, jd: "CompiledJD") -> None:
        self.jd = jd
        must = jd.must_have_skills_dict()
        nice = jd.nice_to_have_skills_dict()
        self.weights = jd.must_have_weights_dict()
        self.normalized_must = {
            group: tuple(_norm(alias) for alias in aliases) for group, aliases in must.items()
        }
        self.normalized_nice = {
            group: tuple(_norm(alias) for alias in aliases) for group, aliases in nice.items()
        }
        self.padded_must = {g: _pad(a) for g, a in self.normalized_must.items()}
        self.padded_nice = {g: _pad(a) for g, a in self.normalized_nice.items()}
        self.split_must = {g: _split_padded(p) for g, p in self.padded_must.items()}
        self.split_nice = {g: _split_padded(p) for g, p in self.padded_nice.items()}
        self.relevant_padded = _pad(
            alias
            for aliases in list(self.normalized_must.values()) + list(self.normalized_nice.values())
            for alias in aliases
        )
        self.split_relevant = _split_padded(self.relevant_padded)
        self.core_padded = _pad(
            alias for aliases in self.normalized_must.values() for alias in aliases
        )
        self.title_padded = {
            _pad([t])[0]: w for t, w in jd.target_title_weights_dict().items() if _pad([t])
        }
        self.locations_padded = _pad(jd.preferred_locations)
        self.yoe_target = jd.yoe_target
        self._relevant_name_cache: dict[str, bool] = {}

    def is_relevant_skill_name(self, name_n: str) -> bool:
        cached = self._relevant_name_cache.get(name_n)
        if cached is None:
            cached = _has_boundary(self.relevant_padded, name_n)
            if len(self._relevant_name_cache) < (1 << 16):
                self._relevant_name_cache[name_n] = cached
        return cached


def _build_default_matchers() -> JDMatchers:
    from redrob_ranker.jd_compiler import DEFAULT_COMPILED_JD

    return JDMatchers(DEFAULT_COMPILED_JD)


_DEFAULT_MATCHERS = _build_default_matchers()
_ALT_MATCHERS: dict[object, JDMatchers] = {}


def _matchers_for(config) -> JDMatchers:
    if config is None or config is _DEFAULT_MATCHERS.jd or config == _DEFAULT_MATCHERS.jd:
        return _DEFAULT_MATCHERS
    m = _ALT_MATCHERS.get(config)
    if m is None:
        m = JDMatchers(config)
        _ALT_MATCHERS[config] = m
    return m


# Back-compat module-level views of the default configuration (tests and
# scripts import these; they are the same objects the default path uses).
NORMALIZED_MUST_HAVE_SKILLS = _DEFAULT_MATCHERS.normalized_must
NORMALIZED_NICE_TO_HAVE_SKILLS = _DEFAULT_MATCHERS.normalized_nice
PADDED_MUST_HAVE_SKILLS = _DEFAULT_MATCHERS.padded_must
PADDED_NICE_TO_HAVE_SKILLS = _DEFAULT_MATCHERS.padded_nice
PADDED_RELEVANT_SKILL_ALIASES = _DEFAULT_MATCHERS.relevant_padded
PADDED_CORE_SKILL_ALIASES = _DEFAULT_MATCHERS.core_padded


def _days_since(date_s: str | None) -> int:
    if not date_s:
        return 9999
    try:
        y, m, d = [int(x) for x in date_s[:10].split("-")]
        return max(0, (REFERENCE_DATE - date(y, m, d)).days)
    except (ValueError, TypeError, IndexError):
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
    parts = [(candidate.get("profile") or {}).get("summary", "")]
    for job in candidate.get("career_history", []) or []:
        parts.extend([job.get("title", ""), job.get("description", ""), job.get("industry", "")])
    return _norm(" ".join(parts))


def _alias_match(
    candidate_terms: set[str],
    token_set: set[str],
    safe_full_text: str,
    aliases: tuple[str, ...],
    split_aliases: tuple[frozenset[str], tuple[str, ...]],
) -> float:
    """Score 1.0 if any alias is a listed skill, else 0.7 on a text mention.

    Equivalent to max() over per-alias scores: set membership first
    (early-exit at 1.0), then the tokenized text check (0.7). Single-word
    aliases use the per-candidate token set; multi-word aliases substring-scan
    the padded text (see _split_padded for the equivalence argument).
    """
    for alias_n in aliases:
        if alias_n in candidate_terms:
            return 1.0
    if _has_tokenized(split_aliases, token_set, safe_full_text):
        return 0.7
    return 0.0


_TARGET_TITLE_PADDED = _DEFAULT_MATCHERS.title_padded
_NON_TARGET_PADDED = _pad(NON_TARGET_TITLES)

def _title_score(candidate: dict, matchers: JDMatchers = _DEFAULT_MATCHERS) -> float:
    profile = candidate.get("profile") or {}
    current = _norm(profile.get("current_title"))
    headline = _norm(profile.get("headline"))
    historical = " ".join(_norm(j.get("title")) for j in candidate.get("career_history", []) or [])
    text = f"{current} {headline} {historical}"

    score = 0.08
    safe_text = f" {text} "
    current_score = 0.08
    safe_current = f" {current} {headline} "
    for pt, weight in matchers.title_padded.items():
        if pt in safe_text:
            score = max(score, weight)
        if pt in safe_current:
            current_score = max(current_score, weight)
    if matchers is not _DEFAULT_MATCHERS and current_score < 0.35 and score > 0.65:
        score = min(score, 0.55)
    elif matchers is not _DEFAULT_MATCHERS and current_score < 0.65 and score > 0.85:
        score = min(score, 0.72)
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


def _honeypot_flags(
    candidate: dict, values: dict[str, float], matchers: JDMatchers = _DEFAULT_MATCHERS
) -> list[str]:
    flags: list[str] = []
    profile = candidate.get("profile") or {}
    signals = candidate.get("redrob_signals") or {}
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
        if _has_boundary(matchers.core_padded, name_n):
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
    if _has_boundary(_NON_TARGET_PADDED, title) and values["ir_ranking_experience"] >= 0.45:
        flags.append("title_description_contradiction")

    return flags


_SENIOR_TITLES_PADDED = _pad(["senior", "staff", "lead", "principal"])
_IR_RANKING_PADDED = _pad([str(t).lower() for t in IR_RANKING_SIGNALS])
_CV_SPEECH_ROBOTICS_PADDED = _pad([str(t).lower() for t in CV_SPEECH_ROBOTICS_TERMS])
_PRODUCTION_PADDED = _pad([str(t).lower() for t in PRODUCTION_SIGNALS])
_PURE_RESEARCH_PADDED = _pad([str(t).lower() for t in PURE_RESEARCH_SIGNALS])
_SCALE_PADDED = _pad([str(t).lower() for t in SCALE_SIGNALS])
_CODE_WRITING_PADDED = _pad([str(t).lower() for t in CODE_WRITING_SIGNALS])
_OPEN_SOURCE_PADDED = _pad([str(t).lower() for t in OPEN_SOURCE_SIGNALS])
_MANAGEMENT_PADDED = _pad(["manager", "lead", "head", "vp", "director"])
_ML_TERMS_PADDED = _pad(["machine learning", "ai", "ml", "nlp", "data science"])
_LOCATIONS_PADDED = _pad(PREFERRED_INDIAN_LOCATIONS)
_LLM_WRAPPER_PADDED = _pad([str(t).lower() for t in LLM_WRAPPER_TERMS])
_JUNIOR_PADDED = _pad(["junior", "intern", "trainee", "associate", "fresher"])
_AI_CURRENT_TITLE_PADDED = _pad([
    "ai research engineer",
    "ai specialist",
    "machine learning engineer",
    "ml engineer",
    "computer vision engineer",
    "data scientist",
])
_GENERIC_ENGINEERING_TITLE_PADDED = _pad([
    "software engineer",
    "senior software engineer",
    "staff software engineer",
    "principal software engineer",
    "software developer",
    "full stack",
    "fullstack",
])
_GENERIC_ANALYTICS_TITLE_PADDED = _pad([
    "analyst",
    "business analyst",
    "reporting analyst",
    "analytics consultant",
])
_DIRECT_BACKEND_TITLE_PADDED = _pad([
    "senior backend engineer",
    "staff backend engineer",
    "principal backend engineer",
    "backend engineer",
    "platform engineer",
    "api developer",
])
_DIRECT_DATA_TITLE_PADDED = _pad([
    "senior data analyst",
    "data analyst",
    "business intelligence developer",
    "bi developer",
    "analytics engineer",
    "data engineer",
    "business analyst",
    "reporting analyst",
])
_NON_DATA_CURRENT_TITLE_PADDED = _pad([
    "software engineer",
    "senior software engineer",
    "software developer",
    "backend engineer",
    "full stack",
    "fullstack",
    "frontend engineer",
    "devops engineer",
    "cloud engineer",
    "mobile developer",
    "qa engineer",
])

_BACKEND_API_PADDED = _pad([
    "rest api", "restful api", "api gateway", "graphql", "grpc", "websocket",
    "microservice", "microservices", "service", "platform", "backend",
    "spring boot", "fastapi", "flask", "django", "express", "nodejs", "node js",
])
_BACKEND_DB_PADDED = _pad([
    "postgres", "postgresql", "mysql", "mongodb", "cassandra", "dynamodb",
    "redis", "kafka", "rabbitmq", "sql", "database", "caching", "cache",
    "sharding", "partitioning", "replica", "read replica",
])
_BACKEND_SCALE_PADDED = _pad([
    "qps", "rps", "p99", "p95", "latency", "throughput", "scale", "scaled",
    "million", "millions", "high availability", "fault tolerant",
    "load balancing", "horizontal scaling", "rate limiting", "concurrent",
])
_BACKEND_INFRA_PADDED = _pad([
    "docker", "kubernetes", "terraform", "aws", "azure", "gcp", "ci cd",
    "ci/cd", "jenkins", "github actions", "deployment", "deployments",
])
_BACKEND_SURFACE_PADDED = _pad([
    "api", "rest", "restful", "graphql", "grpc", "json", "xml", "http", "https",
    "oauth", "jwt", "sso", "authentication", "authorization", "backend",
    "server side", "server", "microservice", "microservices", "service",
    "services", "endpoint", "endpoints", "middleware", "database", "db", "sql",
    "nosql", "postgres", "postgresql", "mysql", "mongodb", "redis", "cassandra",
    "dynamodb", "sqlite", "oracle", "mssql", "elasticsearch", "cache", "caching",
    "memcached", "kafka", "rabbitmq", "sqs", "sns", "message queue", "event",
    "pubsub", "pub sub", "docker", "kubernetes", "k8s", "ci cd", "ci/cd",
    "jenkins", "gitlab", "github actions", "terraform", "ansible", "aws", "gcp",
    "azure", "cloud", "ec2", "s3", "lambda", "java", "spring", "spring boot",
    "hibernate", "jpa", "maven", "gradle", "python", "django", "flask",
    "fastapi", "celery", "nodejs", "node js", "express", "nestjs", "typescript",
    "go", "golang", "gin", "ruby", "rails", "php", "laravel", "symfony", "c#",
    ".net", "asp.net", "git", "github", "bitbucket", "agile", "scrum", "jira",
    "confluence", "unit test", "integration test", "tdd", "bdd", "swagger",
    "postman", "openapi",
])
_FRONTEND_PADDED = _pad([
    "frontend", "front end", "react", "angular", "vue", "html", "css",
    "figma", "ui", "ux", "wordpress", "shopify",
])
_NON_BACKEND_ENGINEERING_PADDED = _pad([
    "android", "ios", "react native", "flutter", "mobile", "qa", "quality assurance",
    "test automation", "selenium", "manual testing", "frontend", "front end", "ui",
    "ux", "wordpress", "shopify",
])

_DATA_SQL_PADDED = _pad([
    "sql", "window function", "cte", "partition by", "rank", "dense rank",
    "lead", "lag", "query optimization", "stored procedure", "index tuning",
])
_DATA_WAREHOUSE_PADDED = _pad([
    "data warehouse", "data warehousing", "snowflake", "bigquery", "redshift",
    "databricks", "star schema", "fact table", "dimension table", "dbt",
])
_DATA_VIZ_PADDED = _pad([
    "tableau", "power bi", "looker", "metabase", "superset", "dashboard",
    "executive dashboard", "self service", "reporting", "kpi", "metrics",
])
_DATA_ETL_PADDED = _pad([
    "etl", "elt", "data pipeline", "pipelines", "airflow", "prefect",
    "dagster", "fivetran", "scheduled refresh", "data quality", "data model",
    "data modeling",
])
_DATA_IMPACT_PADDED = _pad([
    "stakeholder", "stakeholders", "business users", "executives", "saved",
    "automated reporting", "hours per week", "decision", "revenue",
    "cost reduction", "self service", "adoption",
])
_DATA_SURFACE_PADDED = _pad([
    "excel", "spreadsheet", "pivot", "vlookup", "macro", "report", "reports",
    "reporting", "dashboard", "dashboards", "kpi", "kpis", "metrics", "okr",
    "okrs", "north star", "business intelligence", "bi", "analytics",
    "data analysis", "insight", "insights", "trend", "trends", "forecast",
    "forecasting", "sql", "mysql", "postgresql", "oracle", "sql server", "tsql",
    "plsql", "query", "queries", "join", "joins", "subquery", "group by",
    "order by", "table", "tables", "schema", "database", "relational", "rdbms",
    "data warehouse", "warehouse", "etl", "elt", "pipeline", "data pipeline",
    "snowflake", "bigquery", "redshift", "azure synapse", "databricks", "dbt",
    "airflow", "talend", "informatica", "ssis", "tableau", "power bi",
    "powerbi", "looker", "qlik", "qlikview", "qliksense", "metabase",
    "superset", "grafana", "kibana", "chart", "charts", "graph",
    "visualization", "sap", "salesforce", "crm", "erp", "google analytics",
    "ga4", "mixpanel", "amplitude", "segment", "looker studio", "data studio",
    "r", "sas", "spss", "stata", "matlab", "python", "pandas", "numpy",
    "statistics", "statistical", "regression", "correlation", "hypothesis",
    "p value", "a b test", "ab test", "experiment", "experimental", "cohort",
    "funnel", "retention", "stakeholder", "stakeholders", "executive",
    "executives", "business user", "presentation", "slide", "deck",
    "storytelling", "narrative",
])

# Tokenized (singles-set, multis-tuple) views of the hot signal lists.
_IR_RANKING_SPLIT = _split_padded(_IR_RANKING_PADDED)
_CV_SPEECH_ROBOTICS_SPLIT = _split_padded(_CV_SPEECH_ROBOTICS_PADDED)
_PRODUCTION_SPLIT = _split_padded(_PRODUCTION_PADDED)
_PURE_RESEARCH_SPLIT = _split_padded(_PURE_RESEARCH_PADDED)
_SCALE_SPLIT = _split_padded(_SCALE_PADDED)
_CODE_WRITING_SPLIT = _split_padded(_CODE_WRITING_PADDED)
_OPEN_SOURCE_SPLIT = _split_padded(_OPEN_SOURCE_PADDED)
_MANAGEMENT_SPLIT = _split_padded(_MANAGEMENT_PADDED)
_LLM_WRAPPER_SPLIT = _split_padded(_LLM_WRAPPER_PADDED)
_AI_CURRENT_TITLE_SPLIT = _split_padded(_AI_CURRENT_TITLE_PADDED)
_GENERIC_ENGINEERING_TITLE_SPLIT = _split_padded(_GENERIC_ENGINEERING_TITLE_PADDED)
_GENERIC_ANALYTICS_TITLE_SPLIT = _split_padded(_GENERIC_ANALYTICS_TITLE_PADDED)
_DIRECT_BACKEND_TITLE_SPLIT = _split_padded(_DIRECT_BACKEND_TITLE_PADDED)
_DIRECT_DATA_TITLE_SPLIT = _split_padded(_DIRECT_DATA_TITLE_PADDED)
_NON_DATA_CURRENT_TITLE_SPLIT = _split_padded(_NON_DATA_CURRENT_TITLE_PADDED)
_BACKEND_API_SPLIT = _split_padded(_BACKEND_API_PADDED)
_BACKEND_DB_SPLIT = _split_padded(_BACKEND_DB_PADDED)
_BACKEND_SCALE_SPLIT = _split_padded(_BACKEND_SCALE_PADDED)
_BACKEND_INFRA_SPLIT = _split_padded(_BACKEND_INFRA_PADDED)
_BACKEND_SURFACE_SPLIT = _split_padded(_BACKEND_SURFACE_PADDED)
_FRONTEND_SPLIT = _split_padded(_FRONTEND_PADDED)
_NON_BACKEND_ENGINEERING_SPLIT = _split_padded(_NON_BACKEND_ENGINEERING_PADDED)
_DATA_SQL_SPLIT = _split_padded(_DATA_SQL_PADDED)
_DATA_WAREHOUSE_SPLIT = _split_padded(_DATA_WAREHOUSE_PADDED)
_DATA_VIZ_SPLIT = _split_padded(_DATA_VIZ_PADDED)
_DATA_ETL_SPLIT = _split_padded(_DATA_ETL_PADDED)
_DATA_IMPACT_SPLIT = _split_padded(_DATA_IMPACT_PADDED)
_DATA_SURFACE_SPLIT = _split_padded(_DATA_SURFACE_PADDED)


def _category_depth(counts: tuple[int, ...], thresholds: tuple[float, ...]) -> float:
    normalized = [clamp(count / threshold) for count, threshold in zip(counts, thresholds)]
    deep_categories = sum(1 for value in normalized if value >= 0.75)
    return clamp(0.55 * (sum(normalized) / max(1, len(normalized))) + 0.45 * (deep_categories / 3.0))

def compute_features(candidate: dict, config=None) -> CandidateFeatures:
    """Score one candidate. `config` is an optional CompiledJD; None means the
    bundled challenge JD (byte-identical to the historical constant path)."""
    if not isinstance(candidate, dict):
        return CandidateFeatures(
            candidate_id=str(candidate) if candidate else "UNKNOWN",
            values={name: 0.0 for name in FEATURE_NAMES},
            behavioral_multiplier=0.0,
            honeypot_multiplier=0.0,
            disqualifier_multiplier=0.0,
            flags=["malformed_candidate"]
        )
    m = _matchers_for(config)
    # `or` guards: demo upload paths can carry explicit nulls (key present,
    # value None); identical for well-formed records.
    profile = candidate.get("profile") or {}
    signals = candidate.get("redrob_signals") or {}
    full_text = _profile_text(candidate)
    career_text = _career_text(candidate)
    # Pad the two large texts once and build their token sets; every boundary
    # helper below reuses them (single-word checks become set lookups).
    # split(" ") -- NOT split() -- so only literal spaces delimit tokens,
    # matching the ' term ' substring semantics exactly (_norm preserves
    # \n/\t, and ' x ' never matched across those).
    safe_full = f" {full_text} "
    safe_career = f" {career_text} "
    tokens_full = set(full_text.split(" "))
    tokens_career = set(career_text.split(" "))
    terms = _skill_terms(candidate)
    career = candidate.get("career_history", []) or []
    skills = _skill_records(candidate)
    values: dict[str, float] = {}

    core_score = 0.0
    for group, aliases in m.normalized_must.items():
        core_score += m.weights[group] * _alias_match(
            terms, tokens_full, safe_full, aliases, m.split_must[group]
        )
    values["core_skill_match"] = clamp(core_score)
    values["jd_keyword_coverage_score"] = clamp(
        _count_tokenized(m.split_relevant, tokens_full, safe_full) / 12.0
    )

    nice_hits = [
        _alias_match(terms, tokens_full, safe_full, aliases, m.split_nice[group])
        for group, aliases in m.normalized_nice.items()
    ]
    values["nice_skill_match"] = clamp(sum(nice_hits) / max(1, len(nice_hits)))

    matched_skill_scores = []

    for skill in skills:
        name = _norm(skill.get("name"))
        if not name:
            continue
        if not m.is_relevant_skill_name(name):
            continue
        prof = {"beginner": 0.35, "intermediate": 0.6, "advanced": 0.85, "expert": 1.0}.get(
            _norm(skill.get("proficiency")), 0.4
        )
        duration = clamp(float(skill.get("duration_months") or 0) / 36.0)
        endorsements = clamp(math.log1p(float(skill.get("endorsements") or 0)) / math.log1p(60))
        matched_skill_scores.append(0.45 * prof + 0.35 * duration + 0.20 * endorsements)
    values["skill_depth_score"] = clamp(sum(matched_skill_scores) / max(1, min(7, len(matched_skill_scores))))

    # Conditional features default to 0.0 so every FEATURE_NAMES entry is set
    # explicitly; the blocks below overwrite them when skills/assessments exist.
    # Byte-identical to the prior .get(name, 0.0) fallbacks, just no longer implicit.
    values["endorsement_trust"] = 0.0
    values["assessment_score_avg"] = 0.0

    if skills:
        credibility = []
        for skill in skills:
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

    cv_count = _count_tokenized(_CV_SPEECH_ROBOTICS_SPLIT, tokens_full, safe_full)

    product_months, consulting_months, total_months = _product_consulting_months(candidate)
    values["product_company_ratio"] = clamp(product_months / max(1, total_months))
    values["consulting_only_flag"] = 1.0 if total_months and consulting_months / total_months > 0.8 and values["product_company_ratio"] < 0.2 else 0.0

    values["ir_ranking_experience"] = clamp(_count_tokenized(_IR_RANKING_SPLIT, tokens_career, safe_career) / 7.0)
    values["production_evidence"] = clamp(_count_tokenized(_PRODUCTION_SPLIT, tokens_career, safe_career) / 8.0)
    if sum(1 for j in career if int(j.get("duration_months") or 0) >= 18) >= 2:
        values["production_evidence"] = clamp(values["production_evidence"] + 0.08)

    title_text = " ".join(_norm(j.get("title")) for j in career)
    current_title = _norm(profile.get("current_title"))
    title_score = _title_score(candidate, m)
    values["title_match_score"] = title_score
    values["senior_title_held"] = 1.0 if _has_boundary(_SENIOR_TITLES_PADDED, f"{current_title} {title_text}") and title_score > 0.55 else 0.0

    completed_tenures = [
        int(j.get("duration_months") or 0)
        for j in career
        if not j.get("is_current")
    ]
    very_short_jobs = sum(1 for months in completed_tenures if months < 9)
    short_jobs = sum(1 for months in completed_tenures if months < 18)
    median_tenure = statistics.median(completed_tenures) if completed_tenures else 0
    total_jobs = len(completed_tenures)
    short_ratio = short_jobs / max(1, total_jobs)
    
    hop_signal = (
        1.0
        if (total_jobs >= 3 and median_tenure < 18) or very_short_jobs >= 3
        else 0.6 if short_jobs >= 3
        else 0.0
    )
    yoe = float(profile.get("years_of_experience") or 0)
    if yoe >= 10.0 and short_ratio <= 0.4 and median_tenure >= 18:
        hop_signal = 0.0

    strong_ranking_or_production = (
        values["production_evidence"] > 0.45 or values["ir_ranking_experience"] > 0.65
    )
    title_hop_penalty = (0.18 if strong_ranking_or_production else 0.35) * hop_signal
    values["career_trajectory_score"] = clamp(0.75 * title_score + 0.25 * values["product_company_ratio"] - title_hop_penalty)
    values["scale_signal"] = clamp(_count_tokenized(_SCALE_SPLIT, tokens_career, safe_career) / 4.0)
    # Multi-word code terms must scan the combined title+career string (a
    # phrase may span the boundary), but single-word terms can use the union
    # of the two token sets.
    safe_title_career = f" {current_title} {career_text} "
    tokens_title_career = tokens_career | set(current_title.split(" "))
    values["code_writing_recent"] = clamp(
        _count_tokenized(_CODE_WRITING_SPLIT, tokens_title_career, safe_title_career) / 4.0
    )

    yoe_target = m.yoe_target  # 7.0 for the bundled JD (band center)
    values["yoe_fit_score"] = 1.0 if yoe >= yoe_target else clamp(math.exp(-((yoe - yoe_target) ** 2) / (2 * 2.6**2)))
    if yoe < 3:
        values["yoe_fit_score"] *= 0.55
    values["education_score"] = _education_score(candidate)

    ml_months = 0
    for job in career:
        text = _norm(" ".join([str(job.get("title", "")), str(job.get("description", ""))]))
        # Boolean context: early-exit boundary check equals nonzero count.
        if _has_boundary(_IR_RANKING_PADDED, text) or _has_boundary(_ML_TERMS_PADDED, text):
            ml_months += int(job.get("duration_months") or 0)
    values["ml_ai_tenure_score"] = clamp(ml_months / 60.0)

    # For compiled non-challenge JDs, reuse the legacy AI evidence fields as
    # role-evidence fields. The default challenge JD path is untouched, so the
    # frozen submission stays byte-identical; backend, DevOps, data/BI, and
    # search JDs now get credit for role-specific delivery evidence in career
    # text instead of only generic AI/retrieval signals.
    if config is not None and not _is_default_jd(config):
        groups = {group for group, _ in getattr(config, "must_have_skills", ())}
        target_titles = tuple(_norm(title) for title, _ in getattr(config, "target_title_weights", ()))
        primary_title = target_titles[0] if target_titles else ""
        primary_backend_role = (
            "senior backend engineer" in primary_title
            or "staff backend engineer" in primary_title
            or "backend engineer" in primary_title
        )
        primary_data_role = (
            "senior data analyst" in primary_title
            or "business intelligence developer" in primary_title
            or "bi developer" in primary_title
        )
        role_evidence_hits = _count_tokenized(m.split_relevant, tokens_career, safe_career)
        if role_evidence_hits:
            values["ir_ranking_experience"] = max(
                values["ir_ranking_experience"],
                clamp(role_evidence_hits / 8.0),
            )
            values["production_evidence"] = max(
                values["production_evidence"],
                clamp(role_evidence_hits / 12.0),
            )

        role_months = 0
        title_terms = tuple(m.title_padded.keys())
        for job in career:
            text = _norm(" ".join([str(job.get("title", "")), str(job.get("description", ""))]))
            safe_job = f" {text} "
            tokens_job = set(text.split(" "))
            if _has_tokenized(m.split_relevant, tokens_job, safe_job) or _has_boundary(title_terms, text):
                role_months += int(job.get("duration_months") or 0)
        if role_months:
            values["ml_ai_tenure_score"] = max(values["ml_ai_tenure_score"], clamp(role_months / 60.0))

        current_tokens = set(current_title.split(" "))
        safe_current = f" {current_title} "

        if "software_backend" in groups and not primary_data_role:
            direct_backend_title = _has_tokenized(_DIRECT_BACKEND_TITLE_SPLIT, current_tokens, safe_current)
            api_hits = _count_tokenized(_BACKEND_API_SPLIT, tokens_full, safe_full)
            db_hits = _count_tokenized(_BACKEND_DB_SPLIT, tokens_full, safe_full)
            scale_hits = _count_tokenized(_BACKEND_SCALE_SPLIT, tokens_full, safe_full)
            infra_hits = _count_tokenized(_BACKEND_INFRA_SPLIT, tokens_full, safe_full)
            surface_hits = _count_tokenized(_BACKEND_SURFACE_SPLIT, tokens_full, safe_full)
            backend_depth = _category_depth(
                (api_hits, db_hits, scale_hits, infra_hits),
                (3.0, 3.0, 2.0, 3.0),
            )
            backend_surface = clamp(surface_hits / 15.0)
            backend_composite = clamp(0.60 * backend_surface + 0.40 * backend_depth)
            api_score = clamp(api_hits / 3.0)
            db_score = clamp(db_hits / 3.0)
            scale_score = clamp(scale_hits / 2.0)
            infra_score = clamp(infra_hits / 3.0)
            values["jd_keyword_coverage_score"] = max(values["jd_keyword_coverage_score"], backend_surface)
            values["ir_ranking_experience"] = max(values["ir_ranking_experience"], backend_composite)
            values["production_evidence"] = max(
                values["production_evidence"],
                clamp(
                    0.26 * api_score
                    + 0.22 * db_score
                    + 0.16 * scale_score
                    + 0.12 * infra_score
                    + 0.24 * backend_surface
                ),
            )
            values["scale_signal"] = max(values["scale_signal"], clamp(max(scale_score, 0.55 * backend_surface)))
            values["code_writing_recent"] = max(
                values["code_writing_recent"],
                clamp(0.50 * api_score + 0.30 * db_score + 0.20 * backend_surface),
            )

            if primary_backend_role and direct_backend_title:
                direct_title_score = 0.98
                values["title_match_score"] = max(values["title_match_score"], direct_title_score)
                values["career_trajectory_score"] = max(
                    values["career_trajectory_score"],
                    clamp(0.75 * direct_title_score + 0.25 * values["product_company_ratio"] - title_hop_penalty),
                )

            generic_engineering_title = _has_tokenized(
                _GENERIC_ENGINEERING_TITLE_SPLIT, current_tokens, safe_current
            )
            fullstack_current_title = "fullstack" in current_tokens or "full stack" in safe_current
            ml_title_qualifier = (
                "ml" in current_tokens
                or "ai" in current_tokens
                or "machine learning" in safe_current
                or "data scientist" in safe_current
            )
            frontend_hits = _count_tokenized(_FRONTEND_SPLIT, tokens_full, safe_full)
            non_backend_hits = _count_tokenized(_NON_BACKEND_ENGINEERING_SPLIT, tokens_full, safe_full)
            backend_term_advantage = (api_hits + db_hits + infra_hits) > (frontend_hits + non_backend_hits + 2)
            strong_generic_backend = (
                values["core_skill_match"] >= 0.72
                or (backend_depth >= 0.80 and (api_hits + db_hits) >= 5)
            )
            if (
                primary_backend_role
                and ml_title_qualifier
                and values["core_skill_match"] < 0.70
                and backend_composite < 0.85
                and values["title_match_score"] > 0.60
            ):
                values["title_match_score"] = 0.60
                values["career_trajectory_score"] = min(
                    values["career_trajectory_score"],
                    clamp(0.75 * values["title_match_score"] + 0.25 * values["product_company_ratio"] - title_hop_penalty),
                )
            if (
                primary_backend_role
                and
                generic_engineering_title
                and backend_term_advantage
                and strong_generic_backend
                and (not fullstack_current_title or values["core_skill_match"] >= 0.72)
                and (not ml_title_qualifier or values["core_skill_match"] >= 0.70)
                and (backend_surface > 0.40 or backend_depth > 0.30)
            ):
                inferred_title_score = 0.92
                values["title_match_score"] = max(values["title_match_score"], inferred_title_score)
                values["career_trajectory_score"] = max(
                    values["career_trajectory_score"],
                    clamp(0.75 * inferred_title_score + 0.25 * values["product_company_ratio"] - title_hop_penalty),
                )

        if "data_bi" in groups:
            direct_data_title = _has_tokenized(_DIRECT_DATA_TITLE_SPLIT, current_tokens, safe_current)
            non_data_current_title = _has_tokenized(
                _NON_DATA_CURRENT_TITLE_SPLIT, current_tokens, safe_current
            )
            sql_hits = _count_tokenized(_DATA_SQL_SPLIT, tokens_full, safe_full)
            warehouse_hits = _count_tokenized(_DATA_WAREHOUSE_SPLIT, tokens_full, safe_full)
            viz_hits = _count_tokenized(_DATA_VIZ_SPLIT, tokens_full, safe_full)
            etl_hits = _count_tokenized(_DATA_ETL_SPLIT, tokens_full, safe_full)
            impact_hits = _count_tokenized(_DATA_IMPACT_SPLIT, tokens_full, safe_full)
            data_surface_hits = _count_tokenized(_DATA_SURFACE_SPLIT, tokens_full, safe_full)
            data_depth = _category_depth(
                (sql_hits, warehouse_hits, viz_hits, etl_hits, impact_hits),
                (2.0, 2.0, 2.0, 2.0, 2.0),
            )
            data_surface = clamp(data_surface_hits / 12.0)
            sql_score = clamp(sql_hits / 2.0)
            warehouse_score = clamp(warehouse_hits / 2.0)
            viz_score = clamp(viz_hits / 2.0)
            etl_score = clamp(etl_hits / 2.0)
            impact_score = clamp(impact_hits / 2.0)
            if primary_data_role and direct_data_title:
                direct_title_score = 0.98
                values["title_match_score"] = max(values["title_match_score"], direct_title_score)
                values["career_trajectory_score"] = max(
                    values["career_trajectory_score"],
                    clamp(0.75 * direct_title_score + 0.25 * values["product_company_ratio"] - title_hop_penalty),
                )
                values["jd_keyword_coverage_score"] = max(values["jd_keyword_coverage_score"], data_surface)
            elif primary_data_role and non_data_current_title and values["title_match_score"] > 0.82:
                values["title_match_score"] = 0.82
                values["career_trajectory_score"] = min(
                    values["career_trajectory_score"],
                    clamp(0.75 * values["title_match_score"] + 0.25 * values["product_company_ratio"] - title_hop_penalty),
                )

            values["ir_ranking_experience"] = max(values["ir_ranking_experience"], data_depth)
            values["production_evidence"] = max(
                values["production_evidence"],
                clamp(
                    0.25 * sql_score
                    + 0.25 * warehouse_score
                    + 0.20 * viz_score
                    + 0.20 * etl_score
                    + 0.10 * impact_score
                ),
            )
            values["scale_signal"] = max(values["scale_signal"], impact_score)
            generic_analytics_title = _has_tokenized(
                _GENERIC_ANALYTICS_TITLE_SPLIT, current_tokens, safe_current
            )
            if (
                primary_data_role
                and
                not non_data_current_title
                and generic_analytics_title
                and (data_surface > 0.50 or data_depth > 0.30)
            ):
                inferred_title_score = 0.90
                values["title_match_score"] = max(values["title_match_score"], inferred_title_score)
                values["career_trajectory_score"] = max(
                    values["career_trajectory_score"],
                    clamp(0.75 * inferred_title_score + 0.25 * values["product_company_ratio"] - title_hop_penalty),
                )
    values["open_source_signal"] = clamp(_count_tokenized(_OPEN_SOURCE_SPLIT, tokens_full, safe_full) / 3.0)

    management_score = _count_tokenized(_MANAGEMENT_SPLIT, tokens_career, safe_career)
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
    preferred_city = _has_boundary(m.locations_padded, location)
    in_india = country == "india" or "india" in country
    willing_relocate = bool(signals.get("willing_to_relocate"))
    values["location_score"] = 1.0 if preferred_city else 0.68 if in_india else 0.42 if willing_relocate else 0.10
    values["relocation_willing"] = 1.0 if willing_relocate else 0.0

    non_target_title = _has_boundary(_NON_TARGET_PADDED, current_title)
    skill_count = len(skills)
    stuffer_signals = 0
    if skill_count >= 12 and values["core_skill_match"] >= 0.55:
        stuffer_signals = 2
        if values["production_evidence"] < 0.30:
            stuffer_signals += 1
        if values["ir_ranking_experience"] < 0.25:
            stuffer_signals += 1
        if values["skill_depth_score"] < 0.45:
            stuffer_signals += 1
        if values.get("endorsement_trust", 0.0) < 0.35:
            stuffer_signals += 1
    values["keyword_stuffer_flag"] = clamp(stuffer_signals / 6.0)

    values["disqualifier_skill_flag"] = 1.0 if (
        cv_count >= 3 and values["ir_ranking_experience"] < 0.3
    ) else 0.0

    hard_flags = _honeypot_flags(candidate, values, m)
    soft_flags: list[str] = []
    if values["consulting_only_flag"]:
        soft_flags.append("consulting_only")
    salary = signals.get("expected_salary_range_inr_lpa", {}) or {}
    if float(salary.get("min") or 0) > float(salary.get("max") or 0) > 0:
        soft_flags.append("salary_inversion")
    if float(signals.get("profile_completeness_score") or 0) < 40 and int(signals.get("endorsements_received") or 0) > 40:
        soft_flags.append("endorsement_inflation_low_profile")
    if _has_tokenized(_PURE_RESEARCH_SPLIT, tokens_career, safe_career) and values["production_evidence"] < 0.35:
        soft_flags.append("pure_research_without_deployment")
    if values["disqualifier_skill_flag"]:
        soft_flags.append("cv_speech_robotics_primary")
    if values["keyword_stuffer_flag"] >= 0.75:
        soft_flags.append("keyword_stuffer")
    if hop_signal >= 1.0:
        soft_flags.append("title_hopper")

    # JD: "AI experience primarily recent (<12mo) LangChain-to-OpenAI" and
    # "framework enthusiasts" are explicitly devalued. Soft, conservative gate:
    # only fires when wrapper terms appear AND there is no shipped retrieval/ranking
    # depth AND ML tenure is short -- so a senior who shipped systems and also lists
    # LangChain is never penalized.
    wrapper_hits = _count_tokenized(_LLM_WRAPPER_SPLIT, tokens_full, safe_full)
    thin_systems = values["production_evidence"] < 0.35 and values["ir_ranking_experience"] < 0.30
    short_ml = values["ml_ai_tenure_score"] < 0.25 or yoe < 4.0
    if wrapper_hits >= 1 and thin_systems and short_ml:
        soft_flags.append("llm_wrapper_only")

    # JD targets a Senior role (5-9 yrs). Soft nudge for early-career profiles that
    # also lack strong systems evidence; a 4-yr engineer who shipped ranking systems
    # (senior_title_held or strong evidence) is intentionally exempt.
    is_junior_title = _has_boundary(_JUNIOR_PADDED, current_title)
    weak_systems_evidence = values["production_evidence"] < 0.6 and values["ir_ranking_experience"] < 0.6
    if (is_junior_title or yoe < 4.0) and not values["senior_title_held"] and weak_systems_evidence:
        soft_flags.append("junior_for_senior_role")

    behavioral_multiplier = compute_behavioral_multiplier(values, candidate)
    honeypot_multiplier = _honeypot_multiplier_for(hard_flags)
    disqualifier_multiplier = compute_disqualifier_multiplier(
        soft_flags, production_evidence=values["production_evidence"]
    )

    return CandidateFeatures(
        candidate_id=candidate["candidate_id"],
        values={name: clamp(values.get(name, 0.0)) for name in FEATURE_NAMES},
        behavioral_multiplier=behavioral_multiplier,
        honeypot_multiplier=honeypot_multiplier,
        disqualifier_multiplier=disqualifier_multiplier,
        flags=hard_flags + soft_flags,
    )


# Honeypot audit remediation (docs/honeypot_audit.md, 2026-06-10): the manual
# review found a plausible honest data-entry explanation for SOME members of
# these two flag classes (single-role abbreviated histories with consistent
# graduation years; uniform zero-duration skill imports). Per the
# pre-registered rule, those classes soften from hard 0.0 to 0.05 -- still an
# effective exclusion (a 0.05x multiplier cannot reach the top-100) but no
# longer an irreversible zero on evidence that admits an innocent reading.
# Classes with self-contradicting evidence (e.g. summary-vs-claim YoE
# mismatch) remain hard zeros.
SOFTENED_HONEYPOT_CLASSES = frozenset({
    "career_history_too_short_for_claimed_yoe",
    "expert_skill_zero_duration",
})


def _honeypot_multiplier_for(hard_flags: list[str]) -> float:
    if not hard_flags:
        return 1.0
    if all(f in SOFTENED_HONEYPOT_CLASSES for f in hard_flags):
        return 0.05
    return 0.0


# Lower clamp of the behavioral multiplier. 0.25 is the shipped behavior; the
# sensitivity sweep (docs/sensitivity_sweep.md) measures alternatives before
# any change is allowed to alter the submission.
BEHAVIORAL_FLOOR_DEFAULT = 0.25


def compute_behavioral_multiplier(
    values: dict[str, float], candidate: dict, floor: float = BEHAVIORAL_FLOOR_DEFAULT
) -> float:
    # Behavior may demote aggressively, but it can only mildly promote; fit must come from base score.
    signals = candidate.get("redrob_signals") or {}
    mult = 1.0
    mult *= 1.05 if signals.get("open_to_work_flag") else 0.90
    mult *= 0.5 + 0.5 * math.sqrt(values["responsiveness_score"])
    mult *= 0.7 + 0.3 * values["profile_quality"]
    mult *= 0.85 + 0.25 * values["availability_score"]
    mult *= 0.8 + 0.2 * values["interview_reliability"]
    mult *= 1.03 if float(signals.get("saved_by_recruiters_30d") or 0) > 5 else 0.97 if float(signals.get("saved_by_recruiters_30d") or 0) == 0 else 1.0
    raw_github = float(signals.get("github_activity_score") or 0)
    mult *= 1.03 if values["github_signal"] > 0.2 else 1.0
    if (candidate.get("redrob_signals") or {}).get("skill_assessment_scores"):
        mult *= 1.05 if values["assessment_score_avg"] > 0.6 else 0.9 if values["assessment_score_avg"] < 0.4 else 1.0
        mult *= _assessment_claim_multiplier(candidate)
    offer_rate = signals.get("offer_acceptance_rate")
    if offer_rate is not None and float(offer_rate) >= 0:
        mult *= 0.85 + 0.30 * clamp(float(offer_rate))
    mult *= 1.02 if values["profile_quality"] > 0.82 else 1.0
    mult *= 1.05 if values["notice_period_score"] >= 1.0 else 0.70 if values["notice_period_score"] <= 0.2 else 1.0
    return clamp(mult, floor, 1.10)


def _assessment_claim_multiplier(candidate: dict) -> float:
    assessments = (candidate.get("redrob_signals") or {}).get("skill_assessment_scores", {}) or {}
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
        mult *= 0.90
    if "salary_inversion" in flags:
        mult *= 0.65
    if "endorsement_inflation_low_profile" in flags:
        mult *= 0.70
    if "llm_wrapper_only" in flags:
        mult *= 0.82
    if "junior_for_senior_role" in flags:
        mult *= 0.88
    if "hidden_text_control_chars" in flags:
        mult *= 0.82
    if "prompt_injection_text" in flags:
        mult *= 0.55
    if "repeated_keyword_block" in flags:
        mult *= 0.65
    return clamp(mult, 0.05, 1.0)


# EXPERIMENTAL: weight of the optional dense-retrieval feature. Only applied when
# semantic_score is provided (--use-embeddings); the default path is unaffected.
SEMANTIC_WEIGHT = 0.10

TRANSFER_SOFT_RISK_FLAGS = {
    "consulting_only",
    "salary_inversion",
    "title_hopper",
    "endorsement_inflation_low_profile",
    "llm_wrapper_only",
    "junior_for_senior_role",
}
TRANSFER_CRITICAL_RISK_FLAGS = {
    "keyword_stuffer",
    "hidden_text_control_chars",
    "prompt_injection_text",
    "repeated_keyword_block",
}


def _is_default_jd(config) -> bool:
    if config is None:
        return True
    from redrob_ranker.jd_compiler import DEFAULT_COMPILED_JD

    return config == DEFAULT_COMPILED_JD


def _alternate_jd_weights(config) -> dict[str, float]:
    """Feature weights for compiled non-challenge JDs.

    The default challenge JD keeps BASE_FEATURE_WEIGHTS exactly. Alternate JDs
    need more mass on compiled title/core-skill/BM25 evidence and less on
    challenge-specific AI tenure/retrieval features.
    """
    groups = {group for group, _ in getattr(config, "must_have_skills", ())}
    target_titles = tuple(_norm(title) for title, _ in getattr(config, "target_title_weights", ()))
    primary_title = target_titles[0] if target_titles else ""
    primary_backend_role = (
        "senior backend engineer" in primary_title
        or "staff backend engineer" in primary_title
        or "backend engineer" in primary_title
    )
    weights = {
        "bm25_score": 0.24,
        "core_skill_match": 0.20,
        "jd_keyword_coverage_score": 0.12,
        "nice_skill_match": 0.04,
        "skill_depth_score": 0.08,
        "endorsement_trust": 0.02,
        "assessment_score_avg": 0.02,
        "github_signal": 0.02,
        "product_company_ratio": 0.04,
        "ir_ranking_experience": 0.02,
        "production_evidence": 0.08,
        "title_match_score": 0.22,
        "senior_title_held": 0.04,
        "career_trajectory_score": 0.06,
        "scale_signal": 0.03,
        "code_writing_recent": 0.05,
        "yoe_fit_score": 0.08,
        "education_score": 0.02,
        "ml_ai_tenure_score": 0.01,
        "open_source_signal": 0.01,
        "location_score": 0.04,
        "relocation_willing": 0.01,
        "notice_period_score": 0.01,
    }
    if "ranking_information_retrieval" in groups:
        weights["ir_ranking_experience"] = 0.10
        weights["bm25_score"] = 0.16
        weights["code_writing_recent"] = 0.04
    if groups & {"embeddings_retrieval", "vector_database", "llm_production"}:
        weights["ml_ai_tenure_score"] = 0.04
        weights["product_company_ratio"] = 0.07
    if groups & {"software_backend", "cloud_devops", "data_bi"}:
        weights["bm25_score"] = 0.16
        weights["core_skill_match"] = 0.12
        weights["jd_keyword_coverage_score"] = 0.24
        weights["ir_ranking_experience"] = 0.10
        weights["production_evidence"] = 0.10
        weights["title_match_score"] = 0.24
        weights["senior_title_held"] = 0.04
        weights["career_trajectory_score"] = 0.04
        weights["ml_ai_tenure_score"] = 0.06
        weights["product_company_ratio"] = 0.02
    if primary_backend_role:
        weights["core_skill_match"] = 0.14
        weights["jd_keyword_coverage_score"] = 0.28
        weights["ir_ranking_experience"] = 0.12
        weights["production_evidence"] = 0.12
        weights["title_match_score"] = 0.16
        weights["career_trajectory_score"] = 0.03
    return weights


def final_score(
    features: CandidateFeatures,
    retrieval_score: float = 0.0,
    semantic_score: float | None = None,
    config=None,
) -> float:
    default_jd = _is_default_jd(config)
    active_weights = BASE_FEATURE_WEIGHTS if default_jd else _alternate_jd_weights(config)
    total_weight = active_weights["bm25_score"]
    weighted_sum = active_weights["bm25_score"] * clamp(retrieval_score)
    for name, weight in active_weights.items():
        if name == "bm25_score":
            continue
        weighted_sum += weight * features.values.get(name, 0.0)
        total_weight += weight
    # Optional dense semantic-fit term. When None (default/official path), the
    # computation is byte-identical to the lexical+feature scorer above.
    if semantic_score is not None:
        weighted_sum += SEMANTIC_WEIGHT * clamp(semantic_score)
        total_weight += SEMANTIC_WEIGHT
    base_score = weighted_sum / total_weight
    if not default_jd:
        groups = {group for group, _ in getattr(config, "must_have_skills", ())}
        title_fit = features.values.get("title_match_score", 0.0)
        role_evidence = features.values.get("ir_ranking_experience", 0.0)
        if title_fit < 0.35:
            base_score *= 0.72 if role_evidence < 0.85 else 0.82
        elif "software_backend" in groups and title_fit < 0.65:
            base_score *= 0.90
    # Guardrails still multiply on top, so a high semantic score cannot rescue a
    # keyword stuffer, honeypot, or disqualified profile.
    behavior_multiplier = features.behavioral_multiplier
    disqualifier_multiplier = features.disqualifier_multiplier
    if not default_jd:
        groups = {group for group, _ in getattr(config, "must_have_skills", ())}
        if groups & {"cloud_devops", "data_bi"}:
            behavior_multiplier = clamp(0.88 + 0.12 * behavior_multiplier, 0.88, 1.03)
        elif "software_backend" in groups:
            title_fit = features.values.get("title_match_score", 0.0)
            role_evidence = features.values.get("ir_ranking_experience", 0.0)
            yoe_fit = features.values.get("yoe_fit_score", 0.0)
            flags = set(features.flags)
            soft_or_clean = not flags or flags <= TRANSFER_SOFT_RISK_FLAGS
            if title_fit >= 0.98 and role_evidence >= 0.70 and yoe_fit >= 0.75 and soft_or_clean:
                behavior_multiplier = max(behavior_multiplier, 0.94)
            elif title_fit >= 0.95 and role_evidence >= 0.50 and yoe_fit >= 0.75 and soft_or_clean:
                behavior_multiplier = max(behavior_multiplier, 0.88)
            elif title_fit >= 0.80 and role_evidence >= 0.60 and yoe_fit >= 0.75 and soft_or_clean:
                behavior_multiplier = max(behavior_multiplier, 0.76)
        if features.flags and not (set(features.flags) & TRANSFER_CRITICAL_RISK_FLAGS):
            if set(features.flags) <= TRANSFER_SOFT_RISK_FLAGS:
                disqualifier_multiplier = max(disqualifier_multiplier, 0.95)
    return max(
        0.0,
        base_score
        * behavior_multiplier
        * features.honeypot_multiplier
        * disqualifier_multiplier,
    )
