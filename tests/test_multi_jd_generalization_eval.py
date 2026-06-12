from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "multi_jd_generalization_eval.py"
    spec = importlib.util.spec_from_file_location("multi_jd_generalization_eval", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = _load_module()


def _candidate(candidate_id: str, title: str, summary: str, skills: list[str]) -> dict:
    return {
        "candidate_id": candidate_id,
        "profile": {
            "current_title": title,
            "headline": title,
            "summary": summary,
            "location": "Pune",
            "country": "India",
            "years_of_experience": 6,
            "current_company": "Acme",
            "current_industry": "Software",
        },
        "career_history": [{
            "company": "Acme",
            "title": title,
            "duration_months": 72,
            "is_current": True,
            "industry": "Software",
            "description": summary,
        }],
        "skills": [
            {"name": skill, "proficiency": "advanced", "endorsements": 10, "duration_months": 36}
            for skill in skills
        ],
        "redrob_signals": {},
    }


def test_role_labeler_scores_matching_backend_profile_above_marketing_profile():
    spec = mod.REFERENCE_ROLES["backend_platform_engineer"]
    good = _candidate(
        "GOOD",
        "Senior Backend Engineer",
        "Built production REST APIs, Kafka services, Spark jobs and distributed microservices.",
        ["Python", "Java", "Kafka", "Spark", "REST API"],
    )
    bad = _candidate(
        "BAD",
        "Marketing Manager",
        "Owned campaign calendars, brand communications and event planning.",
        ["SEO", "Content Marketing"],
    )

    good_tier, good_rel = mod.label_candidate(good, spec)
    bad_tier, bad_rel = mod.label_candidate(bad, spec)

    assert good_tier >= 3
    assert good_rel > bad_rel
    assert bad_tier == 0


def test_keyword_baseline_orders_obvious_skill_match_first():
    spec = mod.REFERENCE_ROLES["data_bi_analyst"]
    good = _candidate(
        "GOOD",
        "BI Developer",
        "Built SQL data warehouse ETL and Power BI dashboards for stakeholder metrics.",
        ["SQL", "Power BI", "ETL", "Data Warehouse"],
    )
    bad = _candidate(
        "BAD",
        "Cloud Engineer",
        "Managed Kubernetes clusters and Terraform modules.",
        ["Kubernetes", "Terraform"],
    )

    assert mod.keyword_baseline_order([bad, good], spec)[0] == "GOOD"
