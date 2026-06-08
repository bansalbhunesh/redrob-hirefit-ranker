"""Tests for grounded API/showpiece payloads."""

from redrob_ranker.features import compute_features
from redrob_ranker.payload import build_candidate_payload


def _candidate() -> dict:
    return {
        "candidate_id": "CAND_0000001",
        "profile": {
            "current_title": "Machine Learning Engineer",
            "headline": "ML Engineer building retrieval systems",
            "summary": "Shipped production embeddings search and ranking systems.",
            "location": "Pune, Maharashtra",
            "country": "India",
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
                "description": "Built production vector search, ranking, and evaluation pipelines.",
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
            {"name": "FAISS", "proficiency": "advanced", "endorsements": 10, "duration_months": 24},
            {"name": "NLP", "proficiency": "advanced", "endorsements": 18, "duration_months": 48},
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


def test_payload_ignores_honeypot_word_in_reasoning_without_feature_flag():
    candidate = _candidate()
    features = compute_features(candidate)

    payload = build_candidate_payload(
        candidate,
        features,
        raw_score=0.8,
        rank=1,
        reasoning="Not a honeypot; strong JD fit.",
        max_score=0.8,
    )

    assert payload["honeypot_flag"] is False
    assert payload["honeypot_reasons"] == []
    assert payload["tier"] == "gold"
    assert payload["multipliers"]["honeypot"] == 1.0
    assert "production_evidence" in payload["features"]


def test_payload_honeypot_comes_from_feature_flags_not_reasoning_text():
    candidate = _candidate()
    candidate["candidate_id"] = "CAND_0000002"
    candidate["redrob_signals"]["expected_salary_range_inr_lpa"] = {"min": 40, "max": 20}
    candidate["career_history"].append(
        {
            "company": "AnotherCo",
            "title": "Machine Learning Engineer",
            "duration_months": 12,
            "is_current": True,
            "description": "Current platform role.",
        }
    )

    features = compute_features(candidate)
    payload = build_candidate_payload(
        candidate,
        features,
        raw_score=0.2,
        rank=8,
        reasoning="Profile has strong skills but consistency concerns.",
        max_score=0.8,
    )

    assert payload["honeypot_flag"] is True
    assert payload["tier"] == "honeypot"
    assert payload["multipliers"]["honeypot"] == 0.0
    assert "Salary Inversion" in payload["honeypot_reasons"]
    assert "Multiple Current Jobs" in payload["honeypot_reasons"]
    assert payload["score"] == 0.25
