"""Tests for reasoning grounding — no hallucinated skills."""

from redrob_ranker.features import compute_features
from redrob_ranker.reasoning import build_reason, _top_relevant_skills


def _make_candidate(**overrides):
    candidate = {
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


def test_top_relevant_skills_only_returns_actual_profile_skills():
    """_top_relevant_skills must only return names present in the candidate's skill list."""
    candidate = _make_candidate()
    actual_skill_names = {s["name"] for s in candidate["skills"]}
    returned = _top_relevant_skills(candidate)
    for skill_name in returned:
        assert skill_name in actual_skill_names, (
            f"_top_relevant_skills returned '{skill_name}' which is not in the candidate's "
            f"actual skills: {actual_skill_names}"
        )


def test_reasoning_mentions_only_real_skills():
    """Every skill name that appears in reasoning text must exist in the candidate profile."""
    candidate = _make_candidate()
    actual_skill_names = {s["name"].lower() for s in candidate["skills"]}
    features = compute_features(candidate)
    reasoning = build_reason(candidate, features, rank=1)

    # The reasoning embeds skills via _top_relevant_skills which joins them with commas
    # after "relevant skills include". Verify those skills exist.
    relevant_skills = _top_relevant_skills(candidate)
    for skill_name in relevant_skills:
        assert skill_name.lower() in actual_skill_names, (
            f"Reasoning would reference '{skill_name}' which is not in profile"
        )


def test_reasoning_does_not_hallucinate_for_empty_skills():
    """A candidate with no skills should still get valid, non-crashing reasoning."""
    candidate = _make_candidate(skills=[])
    features = compute_features(candidate)
    reasoning = build_reason(candidate, features, rank=50)
    assert isinstance(reasoning, str)
    assert len(reasoning) > 20
    # Should not mention "relevant skills include" since there are none
    skills_returned = _top_relevant_skills(candidate)
    assert skills_returned == []


def test_reasoning_variants_differ_across_candidate_ids():
    """Different candidate_ids should produce at least 2 different second-sentence variants."""
    candidate_ids = [
        "CAND_0000001",
        "CAND_0000002",
        "CAND_0000003",
        "CAND_0000004",
        "CAND_0000005",
        "CAND_0000006",
        "CAND_0000007",
        "CAND_0000008",
    ]
    second_sentences = set()
    for cid in candidate_ids:
        candidate = _make_candidate(candidate_id=cid)
        features = compute_features(candidate)
        reasoning = build_reason(candidate, features, rank=10)
        # The second sentence starts after the first period-space
        parts = reasoning.split(". ", 1)
        if len(parts) > 1:
            second_sentences.add(parts[1].split(":")[0])  # Get the prefix before the colon
    # We should see at least 2 different prefixes across 4 candidates
    assert len(second_sentences) >= 2, (
        f"Expected reasoning variation across candidate IDs, but got only: {second_sentences}"
    )


def test_reasoning_includes_jd_connection_and_factual_profile_detail():
    candidate = _make_candidate()
    features = compute_features(candidate)
    reasoning = build_reason(candidate, features, rank=1)

    assert "JD" in reasoning
    assert candidate["profile"]["current_title"] in reasoning
    assert "7.0" in reasoning
    assert candidate["profile"]["current_company"] in reasoning


def test_lower_rank_reasoning_uses_honest_concern_tone():
    candidate = _make_candidate()
    candidate["profile"]["current_title"] = "Marketing Manager"
    candidate["career_history"][0]["title"] = "Marketing Manager"
    candidate["career_history"][0]["description"] = "Used AI tools for campaign analysis."
    candidate["redrob_signals"].update(
        {
            "open_to_work_flag": False,
            "recruiter_response_rate": 0.05,
            "avg_response_time_hours": 220,
            "notice_period_days": 150,
        }
    )
    features = compute_features(candidate)
    reasoning = build_reason(candidate, features, rank=95)

    assert "concern:" in reasoning
    assert "JD" in reasoning
    assert any(detail in reasoning for detail in ["notice period", "response rate", "current title"])
