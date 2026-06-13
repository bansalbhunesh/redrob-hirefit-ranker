#!/usr/bin/env python3
"""Multi-JD generalization benchmark over the Redrob candidate pool.

This is a transfer test, not an official hidden-label claim. Each benchmark JD
gets an independent, role-specific rubric that reads raw profile fields and does
not import redrob_ranker.features. The shipped ranker is then evaluated against
those labels and a simple keyword baseline.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.eval_harness import LabelSet, evaluate  # noqa: E402
from redrob_ranker.io import iter_candidates  # noqa: E402
from redrob_ranker.jd_compiler import compile_jd  # noqa: E402
from redrob_ranker.pipeline import RankerConfig, rank_candidates  # noqa: E402
from redrob_ranker.text import candidate_text  # noqa: E402

TOKEN_RE = re.compile(r"[a-z0-9+#.]{2,}")
REFERENCE_DATE = date(2026, 6, 8)
REFERENCE_ROLES: dict[str, dict[str, object]] = {
    "senior_ai_engineer": {
        "jd": """
Senior AI Engineer, 5-9 years. Build production LLM, retrieval, embeddings,
vector database, ranking and evaluation systems in Python. Location India.
""",
        "titles": ("machine learning engineer", "ml engineer", "ai engineer", "applied scientist",
                   "data scientist", "search engineer", "relevance engineer"),
        "skills": ("python", "pytorch", "tensorflow", "sklearn", "embedding", "embeddings",
                   "vector search", "faiss", "milvus", "pinecone", "llm", "rag", "ranking",
                   "retrieval", "recommendation", "ndcg", "mrr"),
        "evidence": ("shipped", "deployed", "production", "ranking", "retrieval",
                     "semantic search", "recommendation", "vector", "a/b", "latency"),
        "yoe": (5.0, 9.0),
    },
    "backend_platform_engineer": {
        "jd": """
Senior Backend Engineer, 4-8 years. Own Python/Java APIs, microservices,
Kafka distributed systems, Spark data processing and internal search relevance.
Bangalore or Chennai.
""",
        "titles": ("backend engineer", "software engineer", "platform engineer",
                   "senior software engineer", "api developer"),
        "skills": ("python", "java", "spring boot", "fastapi", "flask", "rest api",
                   "microservices", "kafka", "spark", "sql", "postgres", "redis"),
        "evidence": ("api", "microservice", "distributed", "kafka", "spark", "production",
                     "latency", "throughput", "scale", "service", "platform"),
        "yoe": (4.0, 8.0),
    },
    "search_relevance_engineer": {
        "jd": """
Search Relevance Engineer, 5-8 years. Improve ranking, re-rank, information
retrieval, Elasticsearch/OpenSearch and offline NDCG/MRR evaluation.
""",
        "titles": ("search engineer", "relevance engineer", "machine learning engineer",
                   "data scientist", "software engineer"),
        "skills": ("ranking", "reranking", "re-ranking", "retrieval", "information retrieval",
                   "elasticsearch", "opensearch", "solr", "bm25", "ndcg", "mrr",
                   "learning to rank", "python"),
        "evidence": ("search relevance", "ranking", "retrieval", "query", "index",
                     "elasticsearch", "opensearch", "ndcg", "mrr", "a/b", "production"),
        "yoe": (5.0, 8.0),
    },
    "data_bi_analyst": {
        "jd": """
Senior BI Data Analyst, 4-8 years. Own SQL analytics, ETL, data warehouse
models, Power BI/Tableau dashboards and stakeholder decision support.
Hyderabad, Pune or Bangalore.
""",
        "titles": ("data analyst", "senior data analyst", "business intelligence developer",
                   "bi developer", "analytics engineer", "data engineer"),
        "skills": ("sql", "power bi", "tableau", "looker", "snowflake", "redshift", "etl",
                   "data warehouse", "analytics", "dashboard", "python", "pandas"),
        "evidence": ("dashboard", "analytics", "data warehouse", "etl", "reporting",
                     "stakeholder", "metrics", "sql", "business intelligence", "production"),
        "yoe": (4.0, 8.0),
    },
    "devops_cloud_engineer": {
        "jd": """
Senior DevOps Engineer, 5-9 years. Own AWS/Azure cloud infrastructure,
Kubernetes, Docker, Terraform, CI/CD and production reliability for services.
""",
        "titles": ("devops engineer", "site reliability engineer", "sre", "cloud engineer",
                   "platform engineer", "infrastructure engineer"),
        "skills": ("aws", "azure", "gcp", "kubernetes", "docker", "terraform", "ci/cd",
                   "jenkins", "linux", "prometheus", "grafana"),
        "evidence": ("infrastructure", "deployment", "reliability", "incident", "monitoring",
                     "ci/cd", "kubernetes", "docker", "terraform", "production", "uptime"),
        "yoe": (5.0, 9.0),
    },
}

NON_TARGET = (
    "marketing manager", "sales executive", "customer support", "graphic designer",
    "hr manager", "accountant", "finance manager", "content writer", "civil engineer",
    "mechanical engineer",
)
PRODUCTION = ("shipped", "deployed", "production", "launched", "served", "scale", "users")
INDIA_CITIES = ("pune", "noida", "delhi", "gurgaon", "gurugram", "mumbai", "hyderabad",
                "bangalore", "bengaluru", "chennai")


@dataclass(frozen=True, slots=True)
class RoleScores:
    role: str
    hirefit: dict[str, object]
    keyword: dict[str, object]
    label_distribution: dict[int, int]
    seconds: float


def _norm(text: object) -> str:
    return " ".join(m.group(0) for m in TOKEN_RE.finditer(str(text or "").lower()))


def _contains_any(blob: str, terms: tuple[str, ...]) -> bool:
    padded = f" {blob} "
    return any(f" {term} " in padded or term in blob for term in terms)


def _count_terms(blob: str, terms: tuple[str, ...]) -> int:
    padded = f" {blob} "
    return sum(1 for term in terms if f" {term} " in padded or term in blob)


def _days_since(value: object) -> int:
    if not value:
        return 9999
    try:
        y, m, d = (int(part) for part in str(value)[:10].split("-"))
    except (TypeError, ValueError):
        return 9999
    return max(0, (REFERENCE_DATE - date(y, m, d)).days)


def _raw_blobs(candidate: dict) -> tuple[str, str, str, str]:
    profile = candidate.get("profile") or {}
    career = candidate.get("career_history") or []
    title_blob = _norm(" ".join(
        [profile.get("current_title", ""), profile.get("headline", "")]
        + [job.get("title", "") for job in career]
    ))
    career_blob = _norm(" ".join(
        [profile.get("summary", "")]
        + [job.get("description", "") for job in career]
    ))
    skill_blob = _norm(" ".join(str(skill.get("name", "")) for skill in candidate.get("skills", []) or []))
    full_blob = _norm(candidate_text(candidate))
    return title_blob, career_blob, skill_blob, full_blob


def _simple_honeypot(candidate: dict) -> bool:
    profile = candidate.get("profile") or {}
    career = candidate.get("career_history") or []
    yoe = float(profile.get("years_of_experience") or 0.0)
    months = sum(int(job.get("duration_months") or 0) for job in career)
    if yoe and months > yoe * 12 + 30:
        return True
    if yoe >= 5 and career and months < yoe * 12 * 0.45:
        return True
    expert_zero = sum(
        1 for skill in candidate.get("skills", []) or []
        if str(skill.get("proficiency", "")).lower() == "expert"
        and int(skill.get("duration_months") or 0) == 0
    )
    return expert_zero >= 5


def label_candidate(candidate: dict, spec: dict[str, object]) -> tuple[int, float]:
    if _simple_honeypot(candidate):
        return 0, 0.0
    profile = candidate.get("profile") or {}
    title_blob, career_blob, skill_blob, full_blob = _raw_blobs(candidate)
    titles = spec["titles"]
    skills = spec["skills"]
    evidence = spec["evidence"]
    yoe_lo, yoe_hi = spec["yoe"]

    current_title = _norm(profile.get("current_title", ""))
    if _contains_any(current_title, NON_TARGET) and not _contains_any(full_blob, titles):
        return 0, 0.0

    points = 0.0
    if _contains_any(current_title, titles):
        points += 2.0
    elif _contains_any(title_blob, titles):
        points += 1.2

    skill_hits = _count_terms(skill_blob, skills)
    text_skill_hits = _count_terms(full_blob, skills)
    points += min(2.0, 0.40 * skill_hits + 0.18 * max(0, text_skill_hits - skill_hits))

    evidence_hits = _count_terms(career_blob, evidence)
    points += min(2.0, evidence_hits * 0.45)
    if _contains_any(career_blob, PRODUCTION):
        points += 0.8

    yoe = float(profile.get("years_of_experience") or 0.0)
    if yoe_lo <= yoe <= yoe_hi:
        points += 1.0
    elif yoe < max(2.0, yoe_lo - 1.0):
        points -= 0.8
    elif yoe > yoe_hi + 3.0:
        points -= 0.3

    location = _norm(profile.get("location", ""))
    country = _norm(profile.get("country", ""))
    if _contains_any(location, INDIA_CITIES) or "india" in country:
        points += 0.4

    if _contains_any(current_title, NON_TARGET):
        points -= 1.0
    if not _contains_any(title_blob, titles) and skill_hits == 0 and evidence_hits <= 1:
        points -= 1.2

    signals = candidate.get("redrob_signals") or {}
    rr = float(signals.get("recruiter_response_rate") or 0.0)
    active_days = _days_since(signals.get("last_active_date"))
    notice = float(signals.get("notice_period_days") or 180)
    completeness = float(signals.get("profile_completeness_score") or 0.0)
    if signals.get("open_to_work_flag") and rr >= 0.45 and active_days <= 60:
        points += 0.7
    elif rr < 0.20 or active_days > 180:
        points -= 0.8
    if notice <= 60:
        points += 0.3
    elif notice > 120:
        points -= 0.3
    if completeness >= 75:
        points += 0.25
    if signals.get("verified_email") and signals.get("verified_phone"):
        points += 0.15

    relevance = max(0.0, min(5.0, points / 9.6 * 5.0))
    tier = max(0, min(5, round(relevance)))
    return tier, relevance


def build_labels(candidates: list[dict], role: str, spec: dict[str, object]) -> LabelSet:
    tiers: dict[str, float] = {}
    gains: dict[str, float] = {}
    for candidate in candidates:
        tier, relevance = label_candidate(candidate, spec)
        cid = candidate["candidate_id"]
        tiers[cid] = float(tier)
        gains[cid] = relevance
    return LabelSet(name=role, tiers=tiers, gains=gains)


def keyword_baseline_order(candidates: list[dict], spec: dict[str, object]) -> list[str]:
    skills = spec["skills"]
    evidence = spec["evidence"]
    titles = spec["titles"]

    def score(candidate: dict) -> tuple[float, str]:
        title_blob, career_blob, skill_blob, full_blob = _raw_blobs(candidate)
        value = (
            2.0 * _count_terms(title_blob, titles)
            + 1.0 * _count_terms(skill_blob, skills)
            + 0.35 * _count_terms(full_blob, skills)
            + 0.40 * _count_terms(career_blob, evidence)
        )
        return -value, candidate["candidate_id"]

    return [c["candidate_id"] for c in sorted(candidates, key=score)]


def evaluate_role(candidates: list[dict], role: str, spec: dict[str, object], workers: int) -> RoleScores:
    start = time.time()
    compiled = compile_jd(str(spec["jd"]), source=f"multi-jd:{role}")
    labels = build_labels(candidates, role, spec)
    ranked, _ = rank_candidates(
        candidates,
        RankerConfig(candidate_pool_size=0, bm25_backend="bm25s", workers=workers,
                     jd=compiled, apply_calibration=False),
    )
    hirefit_ids = [candidate["candidate_id"] for candidate, _, _ in ranked]
    keyword_ids = keyword_baseline_order(candidates, spec)
    hirefit = evaluate(hirefit_ids, labels, unlabeled="exclude").as_row()
    keyword = evaluate(keyword_ids, labels, unlabeled="exclude").as_row()
    return RoleScores(
        role=role,
        hirefit=hirefit,
        keyword=keyword,
        label_distribution=dict(sorted(Counter(int(v) for v in labels.tiers.values()).items())),
        seconds=round(time.time() - start, 2),
    )


def write_markdown(path: Path, summary: dict) -> None:
    lines = [
        "# Multi-JD Generalization Evaluation",
        "",
        "This is a Redrob-pool transfer benchmark using independent role rubrics.",
        "It is not official hidden-label evidence and it does not tune the ranker.",
        "",
        f"- Candidates scored per JD: {summary['candidate_count']:,}",
        f"- Roles: {len(summary['roles'])}",
        f"- Mean HireFit composite: {summary['mean_hirefit_composite']:.4f}",
        f"- Mean keyword-baseline composite: {summary['mean_keyword_composite']:.4f}",
        "",
        "| role | HireFit composite | keyword composite | "
        "HireFit NDCG@10 | keyword NDCG@10 | HireFit NDCG@50 | keyword NDCG@50 | "
        "HireFit MAP | keyword MAP | HireFit P@10 | keyword P@10 | seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["roles"]:
        lines.append(
            f"| {row['role']} | {row['hirefit']['composite']:.4f} | "
            f"{row['keyword']['composite']:.4f} | {row['hirefit']['ndcg10']:.4f} | "
            f"{row['keyword']['ndcg10']:.4f} | {row['hirefit']['ndcg50']:.4f} | "
            f"{row['keyword']['ndcg50']:.4f} | {row['hirefit']['map']:.4f} | "
            f"{row['keyword']['map']:.4f} | {row['hirefit']['p10']:.4f} | "
            f"{row['keyword']['p10']:.4f} | {row['seconds']:.1f} |"
        )
    lines.extend([
        "",
        "## Limits",
        "",
        "- Labels are role-specific proxy labels built from raw profile fields, not hidden judge labels.",
        "- No candidate IDs or submitted ranks are used in the labeler.",
        "- The challenge JD remains governed by the golden submission; this benchmark is transfer evidence.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run multi-JD generalization eval.")
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--max-candidates", type=int, default=20_000)
    parser.add_argument("--roles", nargs="*", default=list(REFERENCE_ROLES))
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--out-json", type=Path, default=ROOT / "artifacts" / "multi_jd_generalization_eval.json")
    parser.add_argument("--out-md", type=Path, default=ROOT / "docs" / "multi_jd_generalization_eval.md")
    args = parser.parse_args()

    candidates = list(iter_candidates(args.candidates, max_candidates=args.max_candidates))
    role_rows: list[dict] = []
    for role in args.roles:
        if role not in REFERENCE_ROLES:
            raise SystemExit(f"Unknown role {role!r}; choices: {', '.join(REFERENCE_ROLES)}")
        result = evaluate_role(candidates, role, REFERENCE_ROLES[role], workers=args.workers)
        role_rows.append({
            "role": result.role,
            "hirefit": result.hirefit,
            "keyword": result.keyword,
            "label_distribution": result.label_distribution,
            "seconds": result.seconds,
        })
        print(
            f"{role}: HireFit={result.hirefit['composite']:.4f} "
            f"keyword={result.keyword['composite']:.4f} seconds={result.seconds:.1f}",
            flush=True,
        )

    mean_hirefit = sum(float(row["hirefit"]["composite"]) for row in role_rows) / len(role_rows)
    mean_keyword = sum(float(row["keyword"]["composite"]) for row in role_rows) / len(role_rows)
    summary = {
        "candidate_count": len(candidates),
        "roles": role_rows,
        "mean_hirefit_composite": round(mean_hirefit, 4),
        "mean_keyword_composite": round(mean_keyword, 4),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
