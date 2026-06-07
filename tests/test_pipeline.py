from pathlib import Path

from redrob_ranker.pipeline import RankerConfig, run_ranking


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
    "redrob_signals": {"last_active_date":"2025-01-01","open_to_work_flag":false,"recruiter_response_rate":0.05,"avg_response_time_hours":200,"interview_completion_rate":0.2,"saved_by_recruiters_30d":0,"notice_period_days":150,"verified_email":false,"verified_phone":false,"linkedin_connected":false,"willing_to_relocate":false}
  }
]
""",
        encoding="utf-8",
    )
    out = tmp_path / "out.csv"
    result = run_ranking(sample, out, RankerConfig(top_k=2, candidate_pool_size=2))
    assert result.rows[0]["candidate_id"] == "CAND_0000001"
    assert out.read_text(encoding="utf-8").startswith("candidate_id,rank,score,reasoning")

