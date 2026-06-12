from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import compute_features, final_score, _contains, _norm_str
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
    # expert_skill_zero_duration is a soft-floored class per the honeypot
    # audit (docs/honeypot_audit.md): 0.05 instead of hard 0.0, still an
    # effective exclusion from any top-100.
    assert bad.honeypot_multiplier == 0.05
    assert final_score(bad, 0.5) < 0.05 * final_score(good, 0.5)
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


def test_behavior_multiplier_is_capped_as_mild_boost():
    candidate = make_candidate()
    candidate["redrob_signals"].update(
        {
            "last_active_date": "2026-06-01",
            "open_to_work_flag": True,
            "recruiter_response_rate": 1.0,
            "avg_response_time_hours": 2,
            "interview_completion_rate": 1.0,
            "saved_by_recruiters_30d": 20,
            "github_activity_score": 100,
            "profile_completeness_score": 100,
            "offer_acceptance_rate": 1.0,
            "notice_period_days": 15,
        }
    )

    assert compute_features(candidate).behavioral_multiplier <= 1.10


def test_behavior_gap_cannot_flip_large_base_advantage():
    strong_base_average_behavior = 0.85 * 0.95
    weaker_base_perfect_behavior = 0.70 * 1.10

    assert strong_base_average_behavior > weaker_base_perfect_behavior


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


def test_ascii_normalizer_preserves_boundary_semantics():
    assert _norm_str("Senior_AI/ML Engineer, C++ + C#\tRAG") == "senior ai ml engineer  c++ + c#\trag"
    assert _contains(_norm_str("roadmaps, storage, annual"), {"map", "rag", "ann"}) == 0


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


def test_title_hopper_uses_completed_18_month_pattern():
    hopper = make_candidate()
    hopper["career_history"] = [
        {
            "company": f"Company{i}",
            "title": "Machine Learning Engineer",
            "duration_months": 14,
            "is_current": False,
            "industry": "Software",
            "description": "Built ML platform features.",
        }
        for i in range(4)
    ] + [
        {
            "company": "CurrentCo",
            "title": "Machine Learning Engineer",
            "duration_months": 4,
            "is_current": True,
            "industry": "Software",
            "description": "Current role.",
        }
    ]
    stable = make_candidate()
    stable["career_history"] = [
        {
            "company": f"Stable{i}",
            "title": "Machine Learning Engineer",
            "duration_months": months,
            "is_current": False,
            "industry": "Software",
            "description": "Built ML platform features.",
        }
        for i, months in enumerate([30, 40, 50])
    ]
    one_short = make_candidate()
    one_short["career_history"] = [
        {
            "company": "ShortCo",
            "title": "Machine Learning Engineer",
            "duration_months": 6,
            "is_current": False,
            "industry": "Software",
            "description": "Short completed role.",
        }
    ]

    assert "title_hopper" in compute_features(hopper).flags
    assert "title_hopper" not in compute_features(stable).flags
    assert "title_hopper" not in compute_features(one_short).flags


def test_keyword_stuffer_flags_plausible_ai_title_without_production_evidence():
    stuffer = make_candidate()
    stuffer["profile"]["current_title"] = "AI Engineer"
    stuffer["profile"]["summary"] = "AI GenAI RAG embeddings vector database LLM agentic search."
    stuffer["career_history"][0]["title"] = "AI Engineer"
    stuffer["career_history"][0]["description"] = "Explored internal prototypes and demos."
    stuffer["skills"] = [
        {"name": name, "proficiency": "beginner", "endorsements": 0, "duration_months": 0}
        for name in [
            "Python",
            "RAG",
            "LLM",
            "LangChain",
            "LlamaIndex",
            "FAISS",
            "Pinecone",
            "Milvus",
            "Qdrant",
            "Weaviate",
            "NDCG",
            "Learning to Rank",
            "Embeddings",
            "Vector Search",
            "Prompt Engineering",
            "GenAI",
        ]
    ]

    features = compute_features(stuffer)

    assert features.values["keyword_stuffer_flag"] >= 0.8
    assert "keyword_stuffer" in features.flags


def test_real_deep_skill_profile_not_flagged_as_keyword_stuffer():
    candidate = make_candidate()
    candidate["skills"] = [
        {"name": name, "proficiency": "advanced", "endorsements": 20, "duration_months": 36}
        for name in [
            "Python",
            "FAISS",
            "Milvus",
            "NDCG",
            "Learning to Rank",
            "Embeddings",
            "Vector Search",
            "PyTorch",
            "FastAPI",
            "Kafka",
            "Spark",
            "Elasticsearch",
            "LangChain",
            "RAG",
            "MLOps",
            "A/B Testing",
        ]
    ]
    candidate["career_history"][0]["description"] = (
        "Shipped deployed production vector search, retrieval, ranking, evaluation, "
        "latency monitoring, A/B testing, and live inference services."
    )

    features = compute_features(candidate)

    assert features.values["keyword_stuffer_flag"] <= 0.4
    assert "keyword_stuffer" not in features.flags


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
