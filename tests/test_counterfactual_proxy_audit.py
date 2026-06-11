from __future__ import annotations

import csv
import json

from scripts.counterfactual_proxy_audit import audit_candidate, main, preferred_india_location
from redrob_ranker.features import compute_features


def make_candidate(**overrides):
    candidate = {
        "candidate_id": "CAND_1234567",
        "profile": {
            "anonymized_name": "Asha Mehta",
            "current_title": "Machine Learning Engineer",
            "headline": "ML engineer building retrieval systems",
            "summary": "Shipped production embeddings search and ranking systems.",
            "location": "Toronto",
            "country": "Canada",
            "years_of_experience": 7.0,
            "current_company": "CRED",
            "current_industry": "Fintech",
        },
        "career_history": [
            {
                "company": "CRED",
                "title": "Machine Learning Engineer",
                "start_date": "2021-01-01",
                "end_date": None,
                "is_current": True,
                "duration_months": 60,
                "industry": "Fintech",
                "company_size": "1001-5000",
                "description": "Built production vector search, ranking, and evaluation pipelines at scale.",
            }
        ],
        "education": [
            {
                "institution": "IIT Delhi",
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "start_year": 2013,
                "end_year": 2017,
                "tier": "tier_1",
            }
        ],
        "skills": [
            {"name": "Python", "proficiency": "advanced", "endorsements": 20, "duration_months": 60},
            {"name": "Milvus", "proficiency": "advanced", "endorsements": 10, "duration_months": 24},
            {"name": "NLP", "proficiency": "advanced", "endorsements": 18, "duration_months": 48},
            {"name": "NDCG", "proficiency": "intermediate", "endorsements": 6, "duration_months": 18},
        ],
        "redrob_signals": {
            "profile_completeness_score": 90,
            "last_active_date": "2026-05-20",
            "open_to_work_flag": True,
            "profile_views_received_30d": 40,
            "applications_submitted_30d": 3,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 12,
            "skill_assessment_scores": {"Python": 82},
            "search_appearance_30d": 120,
            "interview_completion_rate": 0.9,
            "saved_by_recruiters_30d": 8,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 35},
            "github_activity_score": 45,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
            "willing_to_relocate": False,
            "endorsements_received": 20,
        },
    }
    for key, value in overrides.items():
        candidate[key] = value
    return candidate


def test_name_neutralization_does_not_move_score():
    rows = audit_candidate(make_candidate())
    name_row = next(row for row in rows if row["variant"] == "name_neutralized")
    assert name_row["score_delta"] == 0.0
    assert name_row["tracked_feature_deltas"]["profile_quality"] == 0.0


def test_preferred_location_variant_moves_location_feature():
    candidate = make_candidate()
    base = compute_features(candidate)
    changed = compute_features(preferred_india_location(candidate))

    assert changed.values["location_score"] > base.values["location_score"]
    rows = audit_candidate(candidate)
    location_row = next(row for row in rows if row["variant"] == "preferred_india_location")
    assert location_row["tracked_feature_deltas"]["location_score"] > 0


def test_cli_writes_counterfactual_rows(tmp_path, monkeypatch):
    input_path = tmp_path / "candidates.jsonl"
    out_path = tmp_path / "audit.csv"
    input_path.write_text(json.dumps(make_candidate()) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "counterfactual_proxy_audit.py",
            "--candidates",
            str(input_path),
            "--out",
            str(out_path),
            "--max-candidates",
            "1",
        ],
    )
    assert main() == 0

    with out_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    assert {row["variant"] for row in rows} == {
        "name_neutralized",
        "location_undisclosed",
        "preferred_india_location",
        "behavioral_neutral",
    }
