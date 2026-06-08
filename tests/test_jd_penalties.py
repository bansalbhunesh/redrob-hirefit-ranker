"""Soft JD penalties: LLM-wrapper-only and junior-for-senior-role.

These are deliberately conservative (soft multipliers, not hard gates): they must
fire on the JD's stated anti-patterns but must NOT punish strong candidates who
merely happen to list a wrapper framework or have fewer years.
"""

from redrob_ranker.features import compute_features


def _cand(**over):
    c = {
        "candidate_id": "CAND_0000001",
        "profile": {"current_title": "ML Engineer", "headline": "", "summary": "",
                    "location": "Pune", "country": "India", "years_of_experience": 7.0,
                    "current_company": "CRED", "current_industry": "Fintech"},
        "career_history": [{"company": "CRED", "title": "ML Engineer", "start_date": "2020-01-01",
                            "end_date": None, "is_current": True, "duration_months": 60,
                            "industry": "Fintech", "company_size": "1001-5000", "description": ""}],
        "education": [], "skills": [],
        "redrob_signals": {"recruiter_response_rate": 0.7, "last_active_date": "2026-05-20",
                           "open_to_work_flag": True, "notice_period_days": 30,
                           "verified_email": True, "profile_completeness_score": 85},
    }
    c["profile"].update(over.pop("profile", {}))
    if "career_history" in over:
        c["career_history"] = over.pop("career_history")
    if "skills" in over:
        c["skills"] = over.pop("skills")
    c.update(over)
    return c


def test_llm_wrapper_only_fires_on_thin_wrapper_profile():
    c = _cand(
        profile={"current_title": "AI Engineer", "years_of_experience": 2.5,
                 "summary": "Built chatbots with LangChain and prompt engineering over the OpenAI API."},
        career_history=[{"company": "Acme", "title": "AI Engineer", "start_date": "2024-01-01",
                         "end_date": None, "is_current": True, "duration_months": 14,
                         "industry": "Software", "company_size": "11-50",
                         "description": "Used LangChain and prompt engineering to wire up GPT demos."}],
        skills=[{"name": "LangChain", "proficiency": "advanced", "endorsements": 5, "duration_months": 12},
                {"name": "Prompt Engineering", "proficiency": "advanced", "endorsements": 4, "duration_months": 10}],
    )
    f = compute_features(c)
    assert "llm_wrapper_only" in f.flags
    assert f.disqualifier_multiplier < 1.0


def test_wrapper_term_does_not_penalize_strong_systems_builder():
    # Senior who shipped retrieval/ranking AND happens to list LangChain -> exempt.
    c = _cand(
        profile={"current_title": "Senior Machine Learning Engineer", "years_of_experience": 8.0,
                 "summary": "Shipped production retrieval and ranking systems serving millions."},
        career_history=[{"company": "Flipkart", "title": "Senior Machine Learning Engineer",
                         "start_date": "2018-01-01", "end_date": None, "is_current": True,
                         "duration_months": 90, "industry": "Ecommerce", "company_size": "10001+",
                         "description": "Built and deployed semantic search, ranking and recommendation "
                                        "in production at scale; also used LangChain for an internal tool."}],
        skills=[{"name": "FAISS", "proficiency": "expert", "endorsements": 30, "duration_months": 60},
                {"name": "LangChain", "proficiency": "intermediate", "endorsements": 3, "duration_months": 6}],
    )
    f = compute_features(c)
    assert "llm_wrapper_only" not in f.flags


def test_junior_title_with_weak_evidence_is_flagged():
    c = _cand(profile={"current_title": "Junior ML Engineer", "years_of_experience": 3.0,
                       "summary": "Assisting on data tasks and model experiments."},
              career_history=[{"company": "Acme", "title": "Junior ML Engineer", "start_date": "2023-01-01",
                               "end_date": None, "is_current": True, "duration_months": 24,
                               "industry": "Software", "company_size": "51-200",
                               "description": "Helped label data and run experiments."}])
    f = compute_features(c)
    assert "junior_for_senior_role" in f.flags
    assert f.disqualifier_multiplier < 1.0


def test_strong_early_career_builder_is_exempt():
    # 4 yrs but shipped ranking systems -> NOT flagged junior (evidence exemption).
    c = _cand(
        profile={"current_title": "Machine Learning Engineer", "years_of_experience": 4.0,
                 "summary": "Shipped production ranking and retrieval systems."},
        career_history=[{"company": "Swiggy", "title": "Machine Learning Engineer", "start_date": "2021-06-01",
                         "end_date": None, "is_current": True, "duration_months": 48,
                         "industry": "Food Tech", "company_size": "5001-10000",
                         "description": "Built, deployed and monitored production retrieval, ranking and "
                                        "recommendation systems serving millions of users at low latency."}],
        skills=[{"name": "Learning to Rank", "proficiency": "advanced", "endorsements": 15, "duration_months": 36}],
    )
    f = compute_features(c)
    assert "junior_for_senior_role" not in f.flags
