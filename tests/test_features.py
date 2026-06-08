from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import compute_features, final_score, _contains
from redrob_ranker.retrieval import retrieve_pool
from redrob_ranker.text import candidate_text, tokenize


def make_candidate(**overrides):
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


def test_feature_matrix_has_stable_28_keys():
    features = compute_features(make_candidate())
    assert set(FEATURE_NAMES) == set(features.values)
    assert len(features.values) == 28
    for name, value in features.values.items():
        assert 0.0 <= value <= 1.0, name


def test_good_candidate_scores_above_trap():
    good = compute_features(make_candidate())
    trap = make_candidate()
    trap["candidate_id"] = "CAND_0000002"
    trap["profile"]["current_title"] = "Marketing Manager"
    trap["career_history"][0]["title"] = "Marketing Manager"
    trap["career_history"][0]["description"] = "Used ChatGPT for content marketing."
    trap["skills"] = [
        {"name": "NLP", "proficiency": "expert", "endorsements": 0, "duration_months": 0}
        for _ in range(12)
    ]
    bad = compute_features(trap)
    assert good.role_fit > bad.role_fit
    assert bad.honeypot_risk > good.honeypot_risk
    assert bad.honeypot_multiplier == 0.0
    assert final_score(bad, 0.5) == 0.0
    assert final_score(good, 0.5) > final_score(bad, 0.5)


def test_behavior_multiplier_downweights_stale_unresponsive_profile():
    good = compute_features(make_candidate())
    stale = make_candidate()
    stale["candidate_id"] = "CAND_0000003"
    stale["redrob_signals"].update(
        {
            "last_active_date": "2025-01-01",
            "open_to_work_flag": False,
            "recruiter_response_rate": 0.02,
            "avg_response_time_hours": 220,
            "notice_period_days": 150,
            "saved_by_recruiters_30d": 0,
        }
    )
    weak = compute_features(stale)
    assert weak.behavioral_multiplier < good.behavioral_multiplier
    assert weak.behavioral_multiplier < 0.75


def test_semantic_concept_expansion_catches_plain_language_retrieval():
    candidate = make_candidate()
    candidate["profile"]["summary"] = (
        "Built a context aware conversational system that finds similar items "
        "using neural representations and a FAISS index."
    )
    rendered = candidate_text(candidate)
    tokens = tokenize(rendered)
    assert "concept_retrieval_system" in tokens
    assert "concept_rag_system" in tokens
    assert "concept_vector_database" in tokens
    assert "neural_representations" in tokens


def test_boundary_matching_blocks_audit_false_positives():
    assert _contains("research scientist planning storage roadmap", {"search", "ann", "rag", "map"}) == 0
    assert _contains("built semantic search with ann retrieval and map evaluation", {"search", "ann", "map"}) == 3


def test_short_aliases_do_not_match_inside_unrelated_words():
    candidate = make_candidate()
    candidate["profile"]["summary"] = "Built storage planning roadmaps for annual reporting."
    candidate["career_history"][0]["description"] = "Research operations with planning and storage roadmaps."
    candidate["skills"] = []

    features = compute_features(candidate)

    assert features.values["core_skill_match"] < 0.25
    assert features.values["ir_ranking_experience"] < 0.3


def test_skill_depth_only_counts_relevant_ai_retrieval_skills():
    irrelevant = make_candidate()
    irrelevant["skills"] = [
        {"name": "Excel", "proficiency": "expert", "endorsements": 80, "duration_months": 96},
        {"name": "Public Speaking", "proficiency": "expert", "endorsements": 70, "duration_months": 96},
        {"name": "Payroll", "proficiency": "expert", "endorsements": 60, "duration_months": 96},
    ]
    relevant = make_candidate()
    relevant["skills"] = [
        {"name": "Python", "proficiency": "expert", "endorsements": 20, "duration_months": 60},
        {"name": "FAISS", "proficiency": "advanced", "endorsements": 12, "duration_months": 30},
        {"name": "NDCG", "proficiency": "advanced", "endorsements": 8, "duration_months": 24},
    ]

    assert compute_features(irrelevant).values["skill_depth_score"] == 0.0
    assert compute_features(relevant).values["skill_depth_score"] > 0.5


def test_audit_edge_cases_for_senior_india_profiles():
    veteran = make_candidate()
    veteran["profile"]["years_of_experience"] = 12.0
    veteran["skills"] = [
        {"name": "GenAI", "proficiency": "advanced", "endorsements": 12, "duration_months": 24},
        {"name": "LangChain", "proficiency": "advanced", "endorsements": 8, "duration_months": 18},
        {"name": "Vector Search", "proficiency": "advanced", "endorsements": 10, "duration_months": 24},
        {"name": "Python", "proficiency": "advanced", "endorsements": 20, "duration_months": 72},
    ]
    veteran["redrob_signals"]["notice_period_days"] = 90

    features = compute_features(veteran)

    assert features.values["core_skill_match"] >= 0.40
    assert features.values["yoe_fit_score"] == 1.0
    assert features.values["notice_period_score"] == 0.85


def test_consulting_only_penalty_softens_when_production_is_real():
    services_candidate = make_candidate()
    services_candidate["profile"]["current_company"] = "TCS"
    services_candidate["profile"]["current_industry"] = "IT Services"
    services_candidate["career_history"] = [
        {
            "company": "TCS",
            "title": "Senior Machine Learning Engineer",
            "start_date": "2020-01-01",
            "end_date": None,
            "is_current": True,
            "duration_months": 72,
            "industry": "IT Services",
            "description": (
                "Shipped deployed production vector search ranking services with "
                "latency monitoring, inference pipelines, live users, and A/B metrics."
            ),
        }
    ]

    features = compute_features(services_candidate)

    assert features.values["consulting_only_flag"] == 1.0
    assert features.values["production_evidence"] > 0.5
    assert features.disqualifier_multiplier == 0.80


def test_cv_terms_do_not_disqualify_real_ir_candidate():
    candidate = make_candidate()
    candidate["profile"]["summary"] = (
        "Built semantic search and vector search systems after earlier computer vision work "
        "with OpenCV, image classification, and speech recognition."
    )
    candidate["career_history"][0]["description"] = (
        "Shipped production semantic search, vector search, ranking, retrieval, ndcg, mrr, "
        "and relevance systems for candidate matching."
    )

    features = compute_features(candidate)

    assert features.values["ir_ranking_experience"] >= 0.3
    assert features.values["disqualifier_skill_flag"] == 0.0
    assert "cv_speech_robotics_primary" not in features.flags


def test_unknown_github_and_offer_acceptance_are_not_behavior_penalties():
    known = make_candidate()
    known["redrob_signals"]["github_activity_score"] = 0
    known["redrob_signals"].pop("offer_acceptance_rate", None)

    unknown = make_candidate()
    unknown["candidate_id"] = "CAND_0000005"
    unknown["redrob_signals"]["github_activity_score"] = -1
    unknown["redrob_signals"]["offer_acceptance_rate"] = -1

    assert compute_features(unknown).behavioral_multiplier == compute_features(known).behavioral_multiplier


def test_large_product_company_gets_product_credit():
    candidate = make_candidate()
    candidate["profile"]["current_company"] = "Google"
    candidate["career_history"][0].update(
        {
            "company": "Google",
            "company_size": "10001+",
            "industry": "Software",
        }
    )

    features = compute_features(candidate)

    assert features.values["product_company_ratio"] > 0.9


def test_honeypot_rules_catch_missing_plan_cases():
    candidate = make_candidate()
    candidate["candidate_id"] = "CAND_0000004"
    candidate["career_history"].append(
        {
            "company": "AnotherCo",
            "title": "ML Engineer",
            "duration_months": 24,
            "is_current": True,
            "description": "Current role",
        }
    )
    candidate["career_history"].append(
        {
            "company": "ConsultingCo",
            "title": "Advisor",
            "duration_months": 12,
            "is_current": True,
            "description": "Advisory role",
        }
    )
    candidate["redrob_signals"]["expected_salary_range_inr_lpa"] = {"min": 40, "max": 20}
    candidate["education"][0]["start_year"] = 2022
    candidate["education"][0]["end_year"] = 2020
    candidate["skills"].append(
        {"name": "FAISS", "proficiency": "expert", "endorsements": 4, "duration_months": 0}
    )
    candidate["skills"].append(
        {"name": "Milvus", "proficiency": "expert", "endorsements": 4, "duration_months": 0}
    )
    features = compute_features(candidate)
    assert features.honeypot_multiplier == 0.0
    assert "salary_inversion" in features.flags
    assert "multiple_current_jobs" in features.flags
    assert "impossible_education_timeline" in features.flags
    assert "expert_skill_zero_duration" in features.flags


def test_salary_inversion_alone_is_soft_not_hard_honeypot():
    candidate = make_candidate()
    candidate["candidate_id"] = "CAND_0000006"
    candidate["redrob_signals"]["expected_salary_range_inr_lpa"] = {"min": 40, "max": 20}

    features = compute_features(candidate)

    assert features.honeypot_multiplier == 1.0
    assert "salary_inversion" in features.flags
    assert features.disqualifier_multiplier < 1.0


def test_endorsement_inflation_is_soft_not_hard_honeypot():
    candidate = make_candidate()
    candidate["candidate_id"] = "CAND_0000007"
    candidate["redrob_signals"]["profile_completeness_score"] = 30
    candidate["redrob_signals"]["endorsements_received"] = 80

    features = compute_features(candidate)

    assert features.honeypot_multiplier == 1.0
    assert "endorsement_inflation_low_profile" in features.flags
    assert features.disqualifier_multiplier < 1.0


def test_assessment_claim_mismatch_penalizes_behavior_multiplier():
    good = make_candidate()
    good["skills"] = [
        {"name": "Python", "proficiency": "advanced", "endorsements": 20, "duration_months": 60}
    ]
    good["redrob_signals"]["skill_assessment_scores"] = {"Python": 86}
    mismatch = make_candidate()
    mismatch["skills"] = [
        {"name": "Python", "proficiency": "expert", "endorsements": 20, "duration_months": 60}
    ]
    mismatch["redrob_signals"]["skill_assessment_scores"] = {"Python": 38}

    assert compute_features(mismatch).behavioral_multiplier < compute_features(good).behavioral_multiplier


def test_bm25_backend_falls_back_to_rank_bm25():
    candidates = [make_candidate(), make_candidate(candidate_id="CAND_0000002")]
    scores, backend = retrieve_pool(candidates, backend="auto")
    assert backend in {"bm25s", "rank_bm25"}
    assert len(scores) == 2


def test_explicit_bm25s_backend_available_for_current_environment():
    candidates = [make_candidate(), make_candidate(candidate_id="CAND_0000002")]
    scores, backend = retrieve_pool(candidates, backend="bm25s")
    assert backend == "bm25s"
    assert len(scores) == 2
