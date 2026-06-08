from pathlib import Path

from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import CandidateFeatures
from redrob_ranker.pipeline import RankerConfig, run_ranking
from redrob_ranker.pipeline import rows_from_ranked


def test_pipeline_writes_valid_small_json(tmp_path: Path):
    sample = tmp_path / "sample.json"
    sample.write_text(
        """
[
  {
    "candidate_id": "CAND_0000001",
    "profile": {"current_title":"Machine Learning Engineer","headline":"ML retrieval","summary":"Built production vector search ranking systems","location":"Pune","country":"India","years_of_experience":7,"current_company":"CRED","current_industry":"Fintech"},
    "career_history": [{"company":"CRED","title":"Machine Learning Engineer","duration_months":60,"description":"Shipped embeddings retrieval and ranking"}],
    "education": [],
    "skills": [{"name":"Python","proficiency":"advanced","endorsements":20,"duration_months":60},{"name":"Milvus","proficiency":"advanced","endorsements":10,"duration_months":30}],
    "redrob_signals": {"last_active_date":"2026-05-20","open_to_work_flag":true,"recruiter_response_rate":0.8,"avg_response_time_hours":12,"interview_completion_rate":0.9,"saved_by_recruiters_30d":5,"notice_period_days":30,"verified_email":true,"verified_phone":true,"linkedin_connected":true,"willing_to_relocate":false}
  },
  {
    "candidate_id": "CAND_0000002",
    "profile": {"current_title":"Marketing Manager","headline":"AI enthusiast","summary":"Uses ChatGPT","location":"Berlin","country":"Germany","years_of_experience":7,"current_company":"TCS","current_industry":"IT Services"},
    "career_history": [{"company":"TCS","title":"Marketing Manager","duration_months":84,"description":"Content marketing"}],
    "education": [],
    "skills": [{"name":"NLP","proficiency":"expert","endorsements":0,"duration_months":0}],
    "redrob_signals": {"last_active_date":"2025-01-01","open_to_work_flag":false,"recruiter_response_rate":0.05,"avg_response_time_hours":200,"interview_completion_rate":0.2,"saved_by_recruiters_30d":0,"notice_period_days":150,"verified_email":false,"verified_phone":false,"linkedin_connected":false,"willing_to_relocate":false,"expected_salary_range_inr_lpa":{"min":40,"max":20}}
  }
]
""",
        encoding="utf-8",
    )
    out = tmp_path / "out.csv"
    result = run_ranking(sample, out, RankerConfig(top_k=1, candidate_pool_size=2))
    assert result.rows[0]["candidate_id"] == "CAND_0000001"
    assert "salary_inversion" in result.raw_ranked[1][1].flags
    assert result.raw_ranked[1][1].disqualifier_multiplier < 1.0
    assert result.honeypots_in_output == 0
    assert out.read_text(encoding="utf-8").startswith("candidate_id,rank,score,reasoning")


def test_rows_normalize_raw_scores_and_use_clean_title_article():
    values = {name: 0.0 for name in FEATURE_NAMES}
    values.update(
        {
            "production_evidence": 1.0,
            "ir_ranking_experience": 1.0,
            "location_score": 1.0,
            "notice_period_score": 1.0,
            "responsiveness_score": 0.8,
        }
    )
    features = CandidateFeatures(
        candidate_id="CAND_0000001",
        values=values,
        behavioral_multiplier=1.0,
        honeypot_multiplier=1.0,
        disqualifier_multiplier=1.0,
        flags=[],
    )
    candidate = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "current_title": "AI Engineer",
            "current_company": "CRED",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 6.0,
        },
        "skills": [],
        "redrob_signals": {"recruiter_response_rate": 0.8, "notice_period_days": 30},
    }
    lower_candidate = {**candidate, "candidate_id": "CAND_0000002"}

    rows = rows_from_ranked(
        [(candidate, features, 1.8), (lower_candidate, features, 1.2)],
        top_k=2,
    )

    assert rows[0]["score"] == "1.000000"
    assert rows[1]["score"] == "0.666667"
    assert "Currently an AI Engineer" in rows[0]["reasoning"]
    assert " a AI " not in rows[0]["reasoning"]
    assert "JD" in rows[0]["reasoning"]
