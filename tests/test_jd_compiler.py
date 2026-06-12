"""Phase 2 acceptance: the JD compiler reproduces the hand-coded program.

The hard gate is byte-identity: compiling the bundled job_description.txt must
yield a CompiledJD equal to the constants-derived default, which (combined
with the golden-output regression in test_submission_gate.py) guarantees a
byte-identical submission.csv. A second JD proves generality.
"""

from __future__ import annotations

from pathlib import Path

from redrob_ranker import constants as C
from redrob_ranker.features import compute_features
from redrob_ranker.jd_compiler import (
    DEFAULT_COMPILED_JD,
    CompiledJD,
    compile_jd_file,
    from_constants,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLED_JD = ROOT / "job_description.txt"

DEMO_JD = """Job Description: Senior Backend Engineer
Company: Acme Logistics
Location: Bangalore or Chennai, India
Experience Required: 4-8 years

You will own our order-routing platform. Strong Python required. You will
design REST APIs, scale our distributed systems on Kafka and Spark, and keep
search relevance for the internal catalog ranking healthy. We value
open-source contributions on GitHub.
"""


def test_bundled_jd_compiles_to_the_handcoded_program():
    compiled = compile_jd_file(BUNDLED_JD)
    assert compiled == DEFAULT_COMPILED_JD
    # spot-check the load-bearing artifacts individually for clearer failures
    assert compiled.jd_query == C.JD_QUERY
    assert compiled.must_have_skills_dict() == {k: list(v) for k, v in C.MUST_HAVE_SKILLS.items()}
    assert compiled.must_have_weights_dict() == C.MUST_HAVE_WEIGHTS
    assert compiled.target_title_weights_dict() == C.TARGET_TITLE_WEIGHTS
    assert set(compiled.preferred_locations) == set(C.PREFERRED_INDIAN_LOCATIONS)
    assert (compiled.yoe_band_lo, compiled.yoe_band_hi, compiled.yoe_target) == (5.0, 9.0, 7.0)


def test_from_constants_roundtrip_is_stable():
    assert from_constants() == DEFAULT_COMPILED_JD


def test_default_config_path_is_unchanged():
    candidate = {
        "candidate_id": "CAND_0000001",
        "profile": {"current_title": "Machine Learning Engineer", "summary": "ranking retrieval",
                    "location": "Pune", "country": "India", "years_of_experience": 7},
        "career_history": [{"company": "CRED", "title": "ML Engineer", "duration_months": 60,
                            "description": "Shipped embeddings retrieval ranking in production"}],
        "skills": [{"name": "Python", "proficiency": "advanced", "endorsements": 10, "duration_months": 48}],
        "redrob_signals": {"open_to_work_flag": True, "recruiter_response_rate": 0.8,
                           "notice_period_days": 30, "last_active_date": "2026-05-20"},
    }
    default = compute_features(dict(candidate))
    explicit = compute_features(dict(candidate), config=DEFAULT_COMPILED_JD)
    assert default.values == explicit.values
    assert default.behavioral_multiplier == explicit.behavioral_multiplier
    assert default.flags == explicit.flags


def test_demo_jd_compiles_to_a_different_program():
    from redrob_ranker.jd_compiler import compile_jd

    compiled = compile_jd(DEMO_JD, source="demo")
    assert isinstance(compiled, CompiledJD)
    assert compiled != DEFAULT_COMPILED_JD
    groups = dict(compiled.must_have_skills)
    # backend JD: python + distributed/search concepts, but no embeddings/vector-db
    assert "python_ml_engineering" in groups
    assert "embeddings_retrieval" not in groups
    assert "vector_database" not in groups
    # weights renormalize over active groups
    assert abs(sum(dict(compiled.must_have_weights).values()) - 1.0) < 1e-4
    # backend title family
    titles = compiled.target_title_weights_dict()
    assert titles.get("senior backend engineer") == 1.0
    weights = compiled.must_have_weights_dict()
    assert weights["software_backend"] > weights["ranking_information_retrieval"]
    assert compiled.jd_query.index("rest api") < compiled.jd_query.index("learning to rank")
    # locations: bangalore expands to both spellings, chennai detected
    assert "bengaluru" in compiled.preferred_locations
    assert "chennai" in compiled.preferred_locations
    # experience band parsed
    assert (compiled.yoe_band_lo, compiled.yoe_band_hi) == (4.0, 8.0)


def test_alternate_jd_changes_scoring_for_backend_profile():
    from redrob_ranker.jd_compiler import compile_jd

    backend_jd = compile_jd(DEMO_JD, source="demo")
    backend_candidate = {
        "candidate_id": "CAND_0000002",
        "profile": {"current_title": "Senior Backend Engineer", "summary": "REST APIs Kafka",
                    "location": "Chennai", "country": "India", "years_of_experience": 6},
        "career_history": [{"company": "Acme", "title": "Backend Engineer", "duration_months": 60,
                            "description": "Built REST APIs on Kafka and Spark in production"}],
        "skills": [{"name": "Python", "proficiency": "advanced", "endorsements": 15, "duration_months": 60},
                   {"name": "Kafka", "proficiency": "advanced", "endorsements": 8, "duration_months": 36}],
        "redrob_signals": {"open_to_work_flag": True, "recruiter_response_rate": 0.7,
                           "notice_period_days": 30, "last_active_date": "2026-05-20"},
    }
    under_default = compute_features(dict(backend_candidate))
    under_backend = compute_features(dict(backend_candidate), config=backend_jd)
    # the backend JD should value this profile's titles and location more
    assert under_backend.values["career_trajectory_score"] >= under_default.values["career_trajectory_score"]
    assert under_backend.values["location_score"] > under_default.values["location_score"]
    # alternate JDs reuse the legacy AI evidence fields as role-evidence fields,
    # without changing the bundled AI challenge scorer.
    assert under_default.values["ir_ranking_experience"] == 0.0
    assert under_default.values["ml_ai_tenure_score"] == 0.0
    assert under_backend.values["ir_ranking_experience"] > under_default.values["ir_ranking_experience"]
    assert under_backend.values["ml_ai_tenure_score"] > under_default.values["ml_ai_tenure_score"]


def test_alternate_jd_title_score_prioritizes_current_role_over_history():
    from redrob_ranker.jd_compiler import compile_jd

    backend_jd = compile_jd(DEMO_JD, source="demo")
    former_software_now_ai = {
        "candidate_id": "CAND_AI_HISTORY",
        "profile": {"current_title": "AI Research Engineer", "headline": "AI Research Engineer",
                    "summary": "Previously built REST APIs and Kafka services",
                    "location": "Chennai", "country": "India", "years_of_experience": 6},
        "career_history": [{"company": "Acme", "title": "Senior Software Engineer",
                            "duration_months": 48,
                            "description": "Built REST APIs on Kafka and Spark in production"}],
        "skills": [{"name": "Python", "proficiency": "advanced", "endorsements": 15,
                    "duration_months": 60}],
        "redrob_signals": {"open_to_work_flag": True, "recruiter_response_rate": 0.7,
                           "notice_period_days": 30, "last_active_date": "2026-05-20"},
    }
    current_backend = {
        **former_software_now_ai,
        "candidate_id": "CAND_BACKEND_CURRENT",
        "profile": {
            **former_software_now_ai["profile"],
            "current_title": "Backend Engineer",
            "headline": "Backend Engineer",
        },
    }

    ai_history = compute_features(dict(former_software_now_ai), config=backend_jd)
    backend_current = compute_features(dict(current_backend), config=backend_jd)

    assert ai_history.values["title_match_score"] < backend_current.values["title_match_score"]
    assert ai_history.values["title_match_score"] <= 0.55
