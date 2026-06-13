#!/usr/bin/env python3
"""Generate second-layer evaluation and role-family artifacts.

This is the safe version of the "universal hiring intelligence" layer:

- role-family rubrics for AI, backend, DevOps, data/BI, and search;
- a label-free annotation pack for blind human/LLM judging;
- clearly marked deterministic proxy labels for development only;
- pairwise proxy labels and hard-negative candidates;
- a no-peeking protocol and downloaded external-dataset inventory.

The script never writes ``submission.csv`` and never calls synthetic labels
"blind". The annotation pack is the artifact to send to judges; proxy labels
are a local dev scaffold until independent labels exist.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DATE = date(2026, 6, 12)
TOKEN_RE = re.compile(r"[a-z0-9+#.]{2,}")


@dataclass(frozen=True, slots=True)
class RoleSpec:
    role_family: str
    jd_id: str
    display_name: str
    jd_text: str
    titles: tuple[str, ...]
    must_skills: tuple[str, ...]
    evidence_terms: tuple[str, ...]
    trap_terms: tuple[str, ...]
    yoe_band: tuple[float, float]


PRODUCT_COMPANIES = (
    "swiggy", "zomato", "ola", "uber", "flipkart", "amazon", "google", "meta",
    "netflix", "spotify", "razorpay", "phonepe", "paytm", "zerodha", "freshworks",
    "zoho", "postman", "hasura", "inmobi", "linkedin", "microsoft", "apple",
    "stripe", "airbnb", "meesho", "nykaa", "dream11", "groww",
)
CONSULTING_FIRMS = (
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "hcl",
    "tech mahindra", "mindtree", "mphasis", "lti", "persistent", "hexaware",
    "genpact", "deloitte", "ey", "kpmg", "pwc", "ibm", "oracle",
)
NON_TARGET_TITLES = (
    "marketing manager", "sales executive", "customer support", "graphic designer",
    "hr manager", "accountant", "finance manager", "content writer", "civil engineer",
    "mechanical engineer", "operations manager",
)
INDIA_CITIES = (
    "pune", "noida", "delhi", "ncr", "gurgaon", "gurugram", "mumbai",
    "hyderabad", "bangalore", "bengaluru", "chennai",
)
PRODUCTION_TERMS = (
    "shipped", "deployed", "production", "launched", "served", "serving",
    "latency", "throughput", "real time", "a/b", "millions", "scale", "users",
    "uptime", "p99", "qps",
)


ROLE_SPECS: dict[str, RoleSpec] = {
    "ai_ml_engineering": RoleSpec(
        role_family="ai_ml_engineering",
        jd_id="senior_ai_engineer_redrob",
        display_name="Senior AI Engineer",
        jd_text=(
            "Senior AI Engineer, 5-9 years. Build production LLM, retrieval, "
            "embeddings, vector database, ranking and evaluation systems in Python."
        ),
        titles=(
            "ai engineer", "ml engineer", "machine learning engineer", "applied scientist",
            "applied ml engineer", "nlp engineer", "search engineer", "relevance engineer",
            "ranking engineer", "retrieval engineer", "data scientist",
        ),
        must_skills=(
            "python", "pytorch", "tensorflow", "scikit learn", "sklearn", "embedding",
            "embeddings", "vector search", "faiss", "pinecone", "weaviate", "qdrant",
            "milvus", "elasticsearch", "bm25", "hybrid search", "retrieval", "ranking",
            "recommender", "recommendation", "ndcg", "mrr", "map", "learning to rank",
            "ltr", "llm", "rag", "fine tuning", "lora", "mlops",
        ),
        evidence_terms=(
            "ranking", "retrieval", "semantic search", "recommendation", "vector",
            "embedding", "matching engine", "nearest neighbor", "learning to rank",
            "evaluation", "ndcg", "mrr", "a/b", "production",
        ),
        trap_terms=(
            "prompt engineering", "chatgpt", "openai api", "claude api", "gans",
            "image classification", "object detection", "yolo", "opencv", "speech recognition",
        ),
        yoe_band=(5.0, 9.0),
    ),
    "backend_engineering": RoleSpec(
        role_family="backend_engineering",
        jd_id="senior_backend_engineer_redrob",
        display_name="Backend Platform Engineer",
        jd_text=(
            "Senior Backend Engineer, 4-8 years. Own APIs, microservices, distributed "
            "systems, databases, caching and production platform reliability."
        ),
        titles=(
            "backend engineer", "senior backend engineer", "platform engineer",
            "software engineer", "senior software engineer", "api engineer",
        ),
        must_skills=(
            "python", "java", "go", "node.js", "nodejs", "fastapi", "flask", "spring boot",
            "rest api", "graphql", "microservices", "distributed systems", "kafka", "redis",
            "postgres", "postgresql", "mysql", "mongodb", "cassandra", "dynamodb",
            "caching", "sharding", "load balancing", "docker", "kubernetes",
        ),
        evidence_terms=(
            "api", "microservice", "distributed", "service", "platform", "latency",
            "throughput", "scale", "database", "cache", "event driven", "production",
        ),
        trap_terms=("wordpress", "shopify", "figma", "photoshop", "illustrator", "ui design"),
        yoe_band=(4.0, 8.0),
    ),
    "devops_cloud": RoleSpec(
        role_family="devops_cloud",
        jd_id="senior_devops_cloud_engineer_redrob",
        display_name="DevOps / Cloud Engineer",
        jd_text=(
            "Senior DevOps Engineer, 5-9 years. Own cloud infrastructure, Kubernetes, "
            "Docker, Terraform, CI/CD, observability and production reliability."
        ),
        titles=(
            "devops engineer", "site reliability engineer", "sre", "cloud engineer",
            "platform engineer", "infrastructure engineer",
        ),
        must_skills=(
            "aws", "azure", "gcp", "kubernetes", "docker", "terraform", "ansible",
            "jenkins", "gitlab ci", "github actions", "ci/cd", "prometheus", "grafana",
            "elk", "datadog", "new relic", "helm", "argo cd", "istio", "linux", "bash",
            "observability", "logging", "tracing",
        ),
        evidence_terms=(
            "infrastructure", "deployment", "reliability", "incident", "monitoring",
            "observability", "ci/cd", "kubernetes", "docker", "terraform", "production",
            "uptime", "slo", "sla",
        ),
        trap_terms=("photoshop", "illustrator", "ui design", "seo", "content marketing"),
        yoe_band=(5.0, 9.0),
    ),
    "data_bi_analytics": RoleSpec(
        role_family="data_bi_analytics",
        jd_id="senior_data_bi_analyst_redrob",
        display_name="Data / BI Analyst",
        jd_text=(
            "Senior Data/BI Analyst, 4-8 years. Own SQL analytics, ETL, warehouse "
            "models, dashboards, metrics and stakeholder decision support."
        ),
        titles=(
            "data analyst", "senior data analyst", "bi analyst", "business intelligence",
            "analytics engineer", "data engineer", "bi developer",
        ),
        must_skills=(
            "sql", "etl", "data warehouse", "data warehousing", "dbt", "snowflake",
            "bigquery", "redshift", "tableau", "power bi", "looker", "dashboard",
            "reporting", "metrics", "kpi", "data modeling", "airflow", "spark", "pandas",
            "statistics", "a/b testing", "experimentation",
        ),
        evidence_terms=(
            "dashboard", "analytics", "data warehouse", "etl", "reporting", "stakeholder",
            "metrics", "sql", "business intelligence", "model", "decision support",
            "production",
        ),
        trap_terms=("photoshop", "illustrator", "ui design", "frontend", "seo", "social media"),
        yoe_band=(4.0, 8.0),
    ),
    "search_relevance": RoleSpec(
        role_family="search_relevance",
        jd_id="search_relevance_engineer_redrob",
        display_name="Search Relevance Engineer",
        jd_text=(
            "Search Relevance Engineer, 5-8 years. Improve retrieval, ranking, "
            "query understanding, Elasticsearch/OpenSearch and offline NDCG/MRR evaluation."
        ),
        titles=(
            "search engineer", "relevance engineer", "search relevance engineer",
            "information retrieval engineer", "ranking engineer", "query understanding engineer",
            "machine learning engineer",
        ),
        must_skills=(
            "elasticsearch", "opensearch", "solr", "lucene", "bm25", "tf idf",
            "vector search", "embedding", "embeddings", "faiss", "pinecone",
            "learning to rank", "ltr", "ndcg", "mrr", "map", "query understanding",
            "intent classification", "autocomplete", "spell correction", "personalization",
            "recommendation", "python", "java",
        ),
        evidence_terms=(
            "search relevance", "ranking", "retrieval", "query", "index", "lucene",
            "elasticsearch", "opensearch", "ndcg", "mrr", "a/b", "production",
            "rerank", "re rank",
        ),
        trap_terms=(
            "prompt engineering", "chatgpt", "openai api", "image classification",
            "object detection", "opencv",
        ),
        yoe_band=(5.0, 8.0),
    ),
}


def _norm(value: object) -> str:
    return " ".join(m.group(0) for m in TOKEN_RE.finditer(str(value or "").lower()))


@lru_cache(maxsize=4096)
def _norm_cached(value: str) -> str:
    return _norm(value)


def _contains(blob: str, term: str) -> bool:
    if " " in term:
        return term in blob
    return f" {term} " in f" {blob} "


def _count_terms(blob: str, terms: Iterable[str], tokens: set[str] | None = None) -> int:
    hits = 0
    padded: str | None = None
    for term in terms:
        normalized = _norm_cached(str(term))
        if not normalized:
            continue
        if " " in normalized:
            if normalized in blob:
                hits += 1
        elif tokens is not None:
            if normalized in tokens:
                hits += 1
        else:
            if padded is None:
                padded = f" {blob} "
            if f" {normalized} " in padded:
                hits += 1
    return hits


def _days_since(value: object) -> int:
    if not value:
        return 9999
    try:
        y, m, d = (int(part) for part in str(value)[:10].split("-"))
    except (TypeError, ValueError):
        return 9999
    return max(0, (REFERENCE_DATE - date(y, m, d)).days)


def iter_candidate_file(path: Path, max_candidates: int | None = None) -> Iterator[dict]:
    count = 0
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list):
            raise ValueError("JSON candidate file must be an array")
        for candidate in data:
            yield candidate
            count += 1
            if max_candidates and count >= max_candidates:
                return
        return

    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
            count += 1
            if max_candidates and count >= max_candidates:
                return


def _text_blobs(candidate: dict) -> dict[str, object]:
    profile = candidate.get("profile") or {}
    career = candidate.get("career_history") or []
    skills = candidate.get("skills") or []
    title_blob = _norm(" ".join(
        [profile.get("current_title", ""), profile.get("headline", "")]
        + [job.get("title", "") for job in career]
    ))
    skill_blob = _norm(" ".join(str(skill.get("name", "")) for skill in skills))
    career_blob = _norm(" ".join(
        [profile.get("summary", "")]
        + [job.get("description", "") for job in career]
        + [job.get("company", "") for job in career]
    ))
    all_blob = _norm(f"{title_blob} {skill_blob} {career_blob}")
    return {
        "title": title_blob,
        "title_tokens": set(title_blob.split()),
        "current_title": _norm(profile.get("current_title", "")),
        "current_title_tokens": set(_norm(profile.get("current_title", "")).split()),
        "skills": skill_blob,
        "skills_tokens": set(skill_blob.split()),
        "career": career_blob,
        "career_tokens": set(career_blob.split()),
        "all": all_blob,
        "all_tokens": set(all_blob.split()),
    }


def summarize_candidate(candidate: dict) -> dict:
    profile = candidate.get("profile") or {}
    career = candidate.get("career_history") or []
    skills = candidate.get("skills") or []
    signals = candidate.get("redrob_signals") or {}
    return {
        "current_title": profile.get("current_title"),
        "headline": profile.get("headline"),
        "years_of_experience": profile.get("years_of_experience"),
        "location": profile.get("location"),
        "country": profile.get("country"),
        "current_company": profile.get("current_company"),
        "top_skills": [str(skill.get("name", "")) for skill in skills[:18] if skill.get("name")],
        "career_titles": [job.get("title") for job in career[:5] if job.get("title")],
        "career_companies": [job.get("company") for job in career[:5] if job.get("company")],
        "career_evidence": [
            str(job.get("description", ""))[:360] for job in career[:3] if job.get("description")
        ],
        "redrob_signals": {
            "open_to_work_flag": signals.get("open_to_work_flag"),
            "notice_period_days": signals.get("notice_period_days"),
            "recruiter_response_rate": signals.get("recruiter_response_rate"),
            "last_active_date": signals.get("last_active_date"),
            "profile_completeness_score": signals.get("profile_completeness_score"),
            "verified_email": signals.get("verified_email"),
            "verified_phone": signals.get("verified_phone"),
        },
    }


def _simple_honeypot(candidate: dict) -> tuple[float, list[str]]:
    flags: list[str] = []
    profile = candidate.get("profile") or {}
    career = candidate.get("career_history") or []
    yoe = float(profile.get("years_of_experience") or 0.0)
    career_months = sum(int(job.get("duration_months") or 0) for job in career)
    if yoe and career_months > yoe * 12 + 30:
        flags.append("career_months_exceed_yoe")
    if yoe >= 5 and career and career_months < yoe * 12 * 0.45:
        flags.append("career_months_too_short_for_yoe")
    expert_zero = sum(
        1 for skill in candidate.get("skills", []) or []
        if str(skill.get("proficiency", "")).lower() == "expert"
        and int(skill.get("duration_months") or 0) == 0
    )
    if expert_zero >= 3:
        flags.append("expert_zero_duration")
    return float(len(flags)), flags


def score_role(
    candidate: dict,
    spec: RoleSpec,
    blobs: dict[str, object] | None = None,
    honeypot: tuple[float, list[str]] | None = None,
) -> dict:
    profile = candidate.get("profile") or {}
    signals = candidate.get("redrob_signals") or {}
    blobs = blobs or _text_blobs(candidate)

    title_hits = _count_terms(
        str(blobs["current_title"]),
        spec.titles,
        blobs["current_title_tokens"],  # type: ignore[arg-type]
    )
    title_history_hits = _count_terms(
        str(blobs["title"]),
        spec.titles,
        blobs["title_tokens"],  # type: ignore[arg-type]
    )
    skill_hits = _count_terms(
        str(blobs["skills"]),
        spec.must_skills,
        blobs["skills_tokens"],  # type: ignore[arg-type]
    )
    text_skill_hits = _count_terms(
        str(blobs["all"]),
        spec.must_skills,
        blobs["all_tokens"],  # type: ignore[arg-type]
    )
    evidence_hits = _count_terms(
        str(blobs["career"]),
        spec.evidence_terms,
        blobs["career_tokens"],  # type: ignore[arg-type]
    )
    production_hits = _count_terms(
        str(blobs["career"]),
        PRODUCTION_TERMS,
        blobs["career_tokens"],  # type: ignore[arg-type]
    )
    trap_term_hits = _count_terms(
        str(blobs["all"]),
        spec.trap_terms,
        blobs["all_tokens"],  # type: ignore[arg-type]
    )
    product_hits = _count_terms(
        str(blobs["career"]),
        PRODUCT_COMPANIES,
        blobs["career_tokens"],  # type: ignore[arg-type]
    )
    consulting_hits = _count_terms(
        str(blobs["career"]),
        CONSULTING_FIRMS,
        blobs["career_tokens"],  # type: ignore[arg-type]
    )
    honeypot_penalty, honeypot_flags = honeypot or _simple_honeypot(candidate)

    points = 0.0
    reasons: list[str] = []
    risk_flags: list[str] = []
    gaps: list[str] = []

    if title_hits:
        points += 2.0
        reasons.append("current_title_matches_role")
    elif title_history_hits:
        points += 1.2
        reasons.append("career_title_matches_role")
    else:
        points -= 0.5
        gaps.append("weak_role_title_match")

    points += min(2.2, skill_hits * 0.22 + max(0, text_skill_hits - skill_hits) * 0.08)
    if skill_hits >= 5:
        reasons.append(f"{skill_hits}_explicit_core_skills")
    else:
        gaps.append("limited_explicit_core_skills")

    points += min(1.8, evidence_hits * 0.32)
    if evidence_hits >= 3:
        reasons.append("role_specific_delivery_evidence")
    else:
        gaps.append("limited_delivery_evidence")

    if production_hits >= 2:
        points += 1.0
        reasons.append("production_scale_evidence")
    elif production_hits == 1:
        points += 0.4
    else:
        gaps.append("no_clear_production_evidence")

    yoe = float(profile.get("years_of_experience") or 0.0)
    low, high = spec.yoe_band
    if low <= yoe <= high:
        points += 1.0
        reasons.append("experience_in_band")
    elif yoe < max(1.0, low - 1.0):
        points -= 0.9
        gaps.append("experience_below_band")
    elif yoe > high + 3.0:
        points -= 0.3
        risk_flags.append("experience_over_band")

    if product_hits:
        points += min(0.5, 0.15 * product_hits)
        reasons.append("product_company_context")
    if consulting_hits >= 2 and evidence_hits < 2:
        points -= 0.8
        risk_flags.append("services_context_without_role_evidence")

    current_title = str(blobs["current_title"])
    if (
        _count_terms(
            current_title,
            NON_TARGET_TITLES,
            blobs["current_title_tokens"],  # type: ignore[arg-type]
        )
        and title_history_hits == 0
    ):
        points -= 1.5
        risk_flags.append("current_title_non_target")
    if trap_term_hits >= 3 and evidence_hits < 2:
        points -= 0.8
        risk_flags.append("trap_terms_without_delivery")
    if skill_hits >= 8 and evidence_hits == 0:
        points -= 1.0
        risk_flags.append("keyword_heavy_no_delivery")
    if honeypot_penalty:
        points -= 1.6 * honeypot_penalty
        risk_flags.extend(honeypot_flags)

    rr = float(signals.get("recruiter_response_rate") or 0.0)
    active_days = _days_since(signals.get("last_active_date"))
    notice = float(signals.get("notice_period_days") or 180.0)
    if signals.get("open_to_work_flag") and rr >= 0.45 and active_days <= 75:
        points += 0.7
        reasons.append("reachable")
    elif rr < 0.20 or active_days > 180:
        points -= 0.8
        risk_flags.append("low_reachability")
    if notice <= 45:
        points += 0.25
    elif notice > 120:
        points -= 0.25
        risk_flags.append("long_notice_period")

    location = _norm(f"{profile.get('location', '')} {profile.get('country', '')}")
    if _count_terms(location, INDIA_CITIES, set(location.split())) or "india" in location:
        points += 0.35

    relevance = max(0.0, min(5.0, points / 8.5 * 5.0))
    if honeypot_penalty >= 2 or "keyword_heavy_no_delivery" in risk_flags and not title_hits:
        tier = min(2, round(relevance))
    else:
        tier = max(0, min(5, round(relevance)))
    if tier >= 5:
        label_name = "exceptional_fit"
    elif tier == 4:
        label_name = "strong_fit"
    elif tier == 3:
        label_name = "plausible_fit"
    elif tier == 2:
        label_name = "weak_fit"
    elif tier == 1:
        label_name = "barely_relevant"
    else:
        label_name = "wrong_role_or_trap"

    return {
        "role_family": spec.role_family,
        "jd_id": spec.jd_id,
        "tier": int(tier),
        "relevance": round(relevance, 4),
        "label_name": label_name,
        "confidence": round(1.0 / (1.0 + math.exp(-(points - 2.5))), 4),
        "reason": "; ".join(reasons or ["adjacent_or_thin_evidence"]),
        "must_have_gaps": sorted(set(gaps)),
        "risk_flags": sorted(set(risk_flags)),
        "component_scores": {
            "title_hits": title_hits,
            "title_history_hits": title_history_hits,
            "skill_hits": skill_hits,
            "text_skill_hits": text_skill_hits,
            "evidence_hits": evidence_hits,
            "production_hits": production_hits,
            "trap_term_hits": trap_term_hits,
            "honeypot_penalty": honeypot_penalty,
            "raw_points": round(points, 4),
        },
    }


def load_submission_ranks(path: Path | None) -> dict[str, int]:
    if not path or not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        return {row["candidate_id"]: int(row["rank"]) for row in rows}


def _push(heap: list[tuple[float, str, dict]], limit: int, score: float, record: dict) -> None:
    item = (float(score), record["candidate_id"], record)
    if len(heap) < limit:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def _keyword_strength(role_scores: dict[str, dict]) -> float:
    return max(
        score["component_scores"]["skill_hits"]
        + 0.45 * score["component_scores"]["text_skill_hits"]
        + 0.75 * score["component_scores"]["trap_term_hits"]
        for score in role_scores.values()
    )


def analyze_candidates(
    candidates_path: Path,
    submission_ranks: dict[str, int],
    sample_size: int,
    max_candidates: int | None,
    seed: int,
) -> tuple[list[dict], list[dict], dict[str, int]]:
    rng = random.Random(seed)  # nosec B311
    per_role_limit = max(40, sample_size // max(1, len(ROLE_SPECS)))
    heap_limits = max(sample_size, per_role_limit * 2)
    role_heaps: dict[str, list[tuple[float, str, dict]]] = {role: [] for role in ROLE_SPECS}
    hard_heap: list[tuple[float, str, dict]] = []
    disagreement_heap: list[tuple[float, str, dict]] = []
    near_threshold_heap: list[tuple[float, str, dict]] = []
    official_records: list[dict] = []
    reservoir: list[dict] = []
    role_distribution: Counter[str] = Counter()
    tier_distribution: Counter[int] = Counter()
    analyzed = 0

    for analyzed, candidate in enumerate(iter_candidate_file(candidates_path, max_candidates), start=1):
        cid = str(candidate.get("candidate_id") or f"UNKNOWN_{analyzed}")
        candidate["candidate_id"] = cid
        blobs = _text_blobs(candidate)
        honeypot = _simple_honeypot(candidate)
        role_scores = {
            role: score_role(candidate, spec, blobs=blobs, honeypot=honeypot)
            for role, spec in ROLE_SPECS.items()
        }
        best_role, best_score = max(
            role_scores.items(),
            key=lambda item: (item[1]["relevance"], item[1]["tier"], item[0]),
        )
        role_distribution[best_role] += 1
        tier_distribution[int(best_score["tier"])] += 1
        keyword = _keyword_strength(role_scores)
        trap_score = max(
            len(score["risk_flags"])
            + 2.0 * score["component_scores"]["honeypot_penalty"]
            + (1.5 if "keyword_heavy_no_delivery" in score["risk_flags"] else 0.0)
            for score in role_scores.values()
        )
        record = {
            "candidate_id": cid,
            "summary": summarize_candidate(candidate),
            "role_scores": role_scores,
            "best_role_family": best_role,
            "best_relevance": best_score["relevance"],
            "best_tier": best_score["tier"],
            "keyword_strength": round(keyword, 4),
            "official_rank": submission_ranks.get(cid),
        }
        official_rank = submission_ranks.get(cid)
        if official_rank is not None:
            official_records.append(record)
        for role, score in role_scores.items():
            _push(role_heaps[role], heap_limits, score["relevance"], record)
        _push(hard_heap, heap_limits, trap_score + 0.25 * keyword, record)
        if keyword >= 7.0 and best_score["relevance"] < 3.0:
            _push(disagreement_heap, heap_limits, keyword - best_score["relevance"], record)
        _push(near_threshold_heap, heap_limits, -abs(best_score["relevance"] - 3.0), record)

        if len(reservoir) < sample_size:
            reservoir.append(record)
        else:
            j = rng.randrange(analyzed)
            if j < sample_size:
                reservoir[j] = record

    selected: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(record: dict, role: str, stratum: str) -> None:
        key = (record["candidate_id"], role)
        if key in seen or len(selected) >= sample_size:
            return
        seen.add(key)
        selected.append({**record, "target_role_family": role, "sample_stratum": stratum})

    for record in sorted(official_records, key=lambda r: (r["official_rank"] or 999999, r["candidate_id"])):
        add(record, "ai_ml_engineering", "official_submission_top100")
    for role, heap in role_heaps.items():
        for _, _, record in sorted(heap, reverse=True):
            add(record, role, f"role_top_{role}")
            if len([r for r in selected if r["target_role_family"] == role]) >= per_role_limit:
                break
    for _, _, record in sorted(disagreement_heap, reverse=True):
        add(record, record["best_role_family"], "keyword_proxy_disagreement")
    for _, _, record in sorted(hard_heap, reverse=True):
        add(record, record["best_role_family"], "hard_negative_candidate")
    for _, _, record in sorted(near_threshold_heap, reverse=True):
        add(record, record["best_role_family"], "near_threshold_candidate")
    for record in reservoir:
        add(record, record["best_role_family"], "random_control")
    for role, heap in role_heaps.items():
        for _, _, record in sorted(heap, reverse=True):
            add(record, role, f"fill_{role}")

    stats = {
        "candidates_analyzed": analyzed,
        "role_distribution": dict(role_distribution),
        "tier_distribution": dict(sorted(tier_distribution.items())),
        "selected_rows": len(selected),
    }
    return selected, reservoir, stats


def role_rubrics() -> dict:
    return {
        role: {
            "rubric_version": "v1",
            "jd_id": spec.jd_id,
            "display_name": spec.display_name,
            "jd_text": spec.jd_text,
            "must_have": list(spec.must_skills[:10]),
            "nice_to_have": list(spec.must_skills[10:18]),
            "evidence_terms": list(spec.evidence_terms),
            "disqualifiers": [
                "unavailable_or_unreachable",
                "wrong_current_role_without_role_history",
                "keyword_heavy_no_delivery",
                "no_production_evidence",
                "impossible_profile_timeline",
            ],
            "title_patterns": list(spec.titles),
            "trap_terms": list(spec.trap_terms),
            "yoe_band": list(spec.yoe_band),
        }
        for role, spec in ROLE_SPECS.items()
    }


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    return n


def build_annotation_rows(selected: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    blind_rows = []
    key_rows = []
    proxy_rows = []
    for i, record in enumerate(selected, start=1):
        role = record["target_role_family"]
        spec = ROLE_SPECS[role]
        score = record["role_scores"][role]
        sample_id = f"SLP_{i:05d}"
        blind_rows.append({
            "sample_id": sample_id,
            "candidate_id": record["candidate_id"],
            "jd_id": spec.jd_id,
            "role_family": role,
            "jd_text": spec.jd_text,
            "candidate_summary": record["summary"],
            "annotation_instruction": (
                "Score this candidate against the JD from 0 to 5. Do not use the "
                "candidate_id, sample stratum, prior rank, or any proxy label."
            ),
            "label_schema": {
                "5": "exceptional fit, should be top 20",
                "4": "strong fit, should be top 100",
                "3": "plausible but not priority",
                "2": "weak fit",
                "1": "barely relevant",
                "0": "wrong role / trap / unavailable / fake fit",
            },
        })
        key_rows.append({
            "sample_id": sample_id,
            "candidate_id": record["candidate_id"],
            "role_family": role,
            "sample_stratum": record["sample_stratum"],
            "official_rank": record["official_rank"],
            "keyword_strength": record["keyword_strength"],
            "best_role_family": record["best_role_family"],
            "best_relevance": record["best_relevance"],
        })
        proxy_rows.append({
            "sample_id": sample_id,
            "candidate_id": record["candidate_id"],
            "jd_id": spec.jd_id,
            "role_family": role,
            "tier": score["tier"],
            "relevance": score["relevance"],
            "label_name": score["label_name"],
            "judge_id": f"role_family_proxy_v1_{role}",
            "judge_type": "deterministic_proxy_rubric_not_blind",
            "confidence": score["confidence"],
            "reason": score["reason"],
            "must_have_gaps": score["must_have_gaps"],
            "risk_flags": score["risk_flags"],
            "component_scores": score["component_scores"],
            "policy": "development proxy only; do not train on frozen human labels",
        })
    return blind_rows, key_rows, proxy_rows


def build_pairwise(proxy_rows: list[dict], pair_count: int) -> list[dict]:
    by_role: dict[str, list[dict]] = defaultdict(list)
    for row in proxy_rows:
        by_role[row["role_family"]].append(row)

    pairs: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(role: str, a: dict, b: dict, reason: str) -> None:
        if len(pairs) >= pair_count or a["candidate_id"] == b["candidate_id"]:
            return
        key = (role, a["candidate_id"], b["candidate_id"])
        rev = (role, b["candidate_id"], a["candidate_id"])
        if key in seen or rev in seen:
            return
        seen.add(key)
        margin = float(a["relevance"]) - float(b["relevance"])
        tie = abs(margin) < 0.20 and int(a["tier"]) == int(b["tier"])
        winner = "tie" if tie else ("candidate_a" if margin > 0 else "candidate_b")
        pairs.append({
            "pair_id": f"PAIR_{len(pairs) + 1:05d}",
            "jd_id": a["jd_id"],
            "role_family": role,
            "candidate_a": a["candidate_id"],
            "candidate_b": b["candidate_id"],
            "winner": winner,
            "tie": tie,
            "proxy_margin": round(abs(margin), 4),
            "judge_id": f"role_family_pairwise_proxy_v1_{role}",
            "judge_type": "deterministic_proxy_rubric_not_blind",
            "reason": reason,
        })

    for role, rows in by_role.items():
        ordered = sorted(rows, key=lambda r: (-float(r["relevance"]), r["candidate_id"]))
        for i in range(0, len(ordered) - 1, 2):
            add(role, ordered[i], ordered[-(i + 1)], "top-vs-bottom role contrast")
        for i in range(len(ordered) - 1):
            add(role, ordered[i], ordered[i + 1], "adjacent near-rank comparison")
    return pairs[:pair_count]


def build_hard_negatives(proxy_rows: list[dict]) -> list[dict]:
    rows = []
    for row in proxy_rows:
        risks = set(row["risk_flags"])
        comps = row["component_scores"]
        if int(row["tier"]) > 2 and not risks:
            continue
        if "keyword_heavy_no_delivery" in risks:
            trap_type = "keyword_stuffer"
        elif "current_title_non_target" in risks:
            trap_type = "wrong_role"
        elif "low_reachability" in risks:
            trap_type = "unavailable"
        elif comps.get("honeypot_penalty", 0) > 0:
            trap_type = "impossible_profile"
        elif "no_clear_production_evidence" in row["must_have_gaps"]:
            trap_type = "no_production_evidence"
        else:
            trap_type = "weak_or_risky_fit"
        rows.append({
            "candidate_id": row["candidate_id"],
            "jd_id": row["jd_id"],
            "role_family": row["role_family"],
            "trap_type": trap_type,
            "should_be_top100": False,
            "severity": "high" if int(row["tier"]) == 0 or comps.get("honeypot_penalty", 0) >= 2 else "medium",
            "evidence": row["reason"],
            "risk_flags": row["risk_flags"],
            "component_scores": row["component_scores"],
            "judge_type": "deterministic_proxy_rubric_not_blind",
        })
    rows.sort(key=lambda r: (r["severity"] != "high", r["candidate_id"]))
    return rows


def external_inventory(manifest_path: Path | None) -> dict:
    if not manifest_path or not manifest_path.exists():
        return {"status": "missing", "sources": []}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_source: dict[tuple[str, str], dict] = {}
    for record in data.get("records", []):
        key = (record.get("kind", "unknown"), record.get("source", "unknown"))
        item = by_source.setdefault(
            key,
            {
                "kind": key[0],
                "source": key[1],
                "files": 0,
                "bytes": 0,
                "example_files": [],
            },
        )
        item["files"] += 1
        item["bytes"] += int(record.get("bytes") or 0)
        if len(item["example_files"]) < 5:
            item["example_files"].append(record.get("file"))
    sources = sorted(by_source.values(), key=lambda x: (x["kind"], x["source"]))
    for item in sources:
        item["mb"] = round(item["bytes"] / 1_000_000, 3)
    return {
        "status": "present",
        "manifest_path": str(manifest_path),
        "source_count": len(sources),
        "total_mb": round(sum(item["bytes"] for item in sources) / 1_000_000, 3),
        "sources": sources,
    }


def no_peeking_protocol(out_dir: Path) -> dict:
    return {
        "protocol_name": "second_layer_frozen_annotation_no_peeking",
        "version": "v1",
        "created_for": "Redrob India Runs Track 1 gap lab",
        "artifacts": {
            "label_free_annotation_pack": "blind_annotation_pack.jsonl",
            "sampling_key": "annotation_sampling_key.jsonl",
            "dev_proxy_labels": "proxy_labels.jsonl",
            "future_frozen_labels": "frozen_human_or_llm_labels.jsonl",
        },
        "rules": [
            "Send only blind_annotation_pack.jsonl to judges; never send proxy_labels.jsonl.",
            "Proxy labels are for local development sanity checks only and are not hidden-label proof.",
            "Freeze human/LLM labels once collected; do not change the sample after seeing labels.",
            "Never train or tune on frozen human/LLM labels.",
            "Use a separate dev-proxy pack for iteration; use frozen labels for final reporting only.",
            "Report NDCG@10, NDCG@50, MAP, P@10, inter-judge agreement, and disagreement cases.",
            "Every experiment must record commit SHA, timestamp, changed files, and metric deltas.",
        ],
        "why_this_closes_the_gap": (
            "It separates sampling, annotation, proxy development labels, and final evaluation. "
            "That is the missing discipline behind the earlier 'blind labels' objection."
        ),
        "out_dir": str(out_dir),
    }


def write_outputs(
    selected: list[dict],
    stats: dict[str, object],
    out_dir: Path,
    pair_count: int,
    external_manifest: Path | None,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    blind_rows, key_rows, proxy_rows = build_annotation_rows(selected)
    pair_rows = build_pairwise(proxy_rows, pair_count)
    hard_rows = build_hard_negatives(proxy_rows)

    counts = {
        "blind_annotation_pack_rows": write_jsonl(out_dir / "blind_annotation_pack.jsonl", blind_rows),
        "annotation_sampling_key_rows": write_jsonl(out_dir / "annotation_sampling_key.jsonl", key_rows),
        "proxy_label_rows": write_jsonl(out_dir / "proxy_labels.jsonl", proxy_rows),
        "pairwise_proxy_rows": write_jsonl(out_dir / "pairwise_proxy_labels.jsonl", pair_rows),
        "hard_negative_rows": write_jsonl(out_dir / "hard_negative_proxy.jsonl", hard_rows),
    }
    (out_dir / "role_family_rubrics.json").write_text(
        json.dumps(role_rubrics(), indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    inventory = external_inventory(external_manifest)
    (out_dir / "external_dataset_inventory.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    protocol = no_peeking_protocol(out_dir)
    (out_dir / "no_peeking_eval_protocol.json").write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    summary = {
        "status": "generated",
        "important_warning": (
            "proxy_labels.jsonl is deterministic heuristic data, not blind proof. "
            "blind_annotation_pack.jsonl is label-free and must be independently judged."
        ),
        "counts": counts,
        "candidate_stats": stats,
        "role_families": list(ROLE_SPECS),
        "external_inventory": {
            "status": inventory["status"],
            "source_count": inventory.get("source_count", 0),
            "total_mb": inventory.get("total_mb", 0),
        },
    }
    (out_dir / "second_layer_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(summary_markdown(summary), encoding="utf-8")
    return summary


def summary_markdown(summary: dict) -> str:
    lines = [
        "# Second-Layer Gap Closure Pack",
        "",
        "> Proxy labels are not blind labels. The blind annotation pack is label-free.",
        "",
        "## Counts",
        "",
    ]
    for key, value in summary["counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        "",
        "## Role Families",
        "",
    ])
    for role in summary["role_families"]:
        lines.append(f"- `{role}`")
    stats = summary["candidate_stats"]
    lines.extend([
        "",
        "## Candidate Stats",
        "",
        f"- candidates analyzed: `{stats['candidates_analyzed']}`",
        f"- selected rows: `{stats['selected_rows']}`",
        "",
        "## Files",
        "",
        "- `blind_annotation_pack.jsonl`: label-free pack for independent judging",
        "- `annotation_sampling_key.jsonl`: sampling strata, keep away from judges",
        "- `proxy_labels.jsonl`: deterministic dev proxy labels only",
        "- `pairwise_proxy_labels.jsonl`: deterministic pairwise dev labels only",
        "- `hard_negative_proxy.jsonl`: trap/weak-fit candidates",
        "- `role_family_rubrics.json`: role-family scoring rubrics",
        "- `no_peeking_eval_protocol.json`: frozen-eval rules",
        "- `external_dataset_inventory.json`: downloaded public data provenance",
    ])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--submission", type=Path, default=ROOT / "submission.csv")
    parser.add_argument(
        "--external-manifest",
        type=Path,
        default=ROOT / "data" / "external" / "download_manifest.json",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts" / "second_layer_pack")
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--pair-count", type=int, default=1500)
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260612)
    args = parser.parse_args(argv)

    if args.sample_size <= 0:
        raise ValueError("--sample-size must be positive")
    if args.pair_count < 0:
        raise ValueError("--pair-count must be non-negative")

    submission_ranks = load_submission_ranks(args.submission)
    selected, _, stats = analyze_candidates(
        args.candidates,
        submission_ranks=submission_ranks,
        sample_size=args.sample_size,
        max_candidates=args.max_candidates,
        seed=args.seed,
    )
    summary = write_outputs(
        selected,
        stats,
        out_dir=args.out_dir,
        pair_count=args.pair_count,
        external_manifest=args.external_manifest,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
