from pathlib import Path
import os
import subprocess
import sys

import pytest

import redrob_ranker.pipeline as pipeline_mod
import redrob_ranker.retrieval as retrieval_mod
from redrob_ranker import hyre_prompts
from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.features import CandidateFeatures
from redrob_ranker.pipeline import RankerConfig, rank_candidates, run_ranking
from redrob_ranker.pipeline import rows_from_ranked


def _synthetic_candidates(n: int) -> list[dict]:
    titles = ["Machine Learning Engineer", "NLP Engineer", "Marketing Manager",
              "Data Scientist", "Search Engineer", "Backend Engineer"]
    cands = []
    for i in range(n):
        cands.append({
            "candidate_id": f"CAND_{i:07d}",
            "profile": {"current_title": titles[i % len(titles)], "headline": "ranking retrieval",
                        "summary": "Built production vector search and ranking systems at scale",
                        "location": "Pune" if i % 2 else "Toronto",
                        "country": "India" if i % 2 else "Canada",
                        "years_of_experience": 4 + (i % 8), "current_company": "CRED",
                        "current_industry": "Fintech", "current_company_size": "501-1000"},
            "career_history": [{"company": "CRED", "title": titles[i % len(titles)],
                                "start_date": "2019-01-01", "end_date": None, "duration_months": 48 + i % 12,
                                "is_current": True, "industry": "Fintech", "company_size": "501-1000",
                                "description": "Shipped embeddings retrieval reranking recommendation in production"}],
            "education": [], "certifications": [], "languages": [],
            "skills": [{"name": "Python", "proficiency": "advanced", "endorsements": 20, "duration_months": 60},
                       {"name": "FAISS", "proficiency": "advanced", "endorsements": 10, "duration_months": 30}],
            "redrob_signals": {"last_active_date": "2026-05-20", "open_to_work_flag": True,
                               "recruiter_response_rate": 0.5 + (i % 5) / 10, "avg_response_time_hours": 12,
                               "interview_completion_rate": 0.9, "saved_by_recruiters_30d": i % 7,
                               "notice_period_days": 30, "verified_email": True, "verified_phone": True,
                               "linkedin_connected": True, "willing_to_relocate": False,
                               "github_activity_score": 40, "profile_completeness_score": 90}})
    return cands


def test_parallel_feature_scoring_matches_serial(monkeypatch):
    # Force the parallel path on a small pool so the equivalence is exercised in CI.
    monkeypatch.setattr(pipeline_mod, "_PARALLEL_MIN_POOL", 8)
    candidates = _synthetic_candidates(64)
    serial, _ = rank_candidates([dict(c) for c in candidates], RankerConfig(candidate_pool_size=0, workers=1))
    parallel, _ = rank_candidates([dict(c) for c in candidates], RankerConfig(candidate_pool_size=0, workers=2))
    assert [c["candidate_id"] for c, _, _ in serial] == [c["candidate_id"] for c, _, _ in parallel]
    for (_, _, s_score), (_, _, p_score) in zip(serial, parallel):
        assert abs(s_score - p_score) < 1e-12


def test_auto_workers_respect_cgroup_cpu_quota(monkeypatch):
    monkeypatch.setattr(pipeline_mod, "_PARALLEL_MIN_POOL", 8)
    monkeypatch.setattr(pipeline_mod.os, "cpu_count", lambda: 16)
    monkeypatch.setattr(pipeline_mod, "_cgroup_cpu_quota_count", lambda: 2)

    assert pipeline_mod._resolve_workers(0, 64) == 2
    assert pipeline_mod._resolve_workers(8, 64) == 2
    assert pipeline_mod._resolve_workers(1, 64) == 1


def test_auto_workers_use_cap_when_no_cgroup_quota(monkeypatch):
    monkeypatch.setattr(pipeline_mod, "_PARALLEL_MIN_POOL", 8)
    monkeypatch.setattr(pipeline_mod.os, "cpu_count", lambda: 16)
    monkeypatch.setattr(pipeline_mod, "_cgroup_cpu_quota_count", lambda: None)

    assert pipeline_mod._resolve_workers(0, 64) == 8


def test_tokenizer_workers_respect_cgroup_cpu_quota(monkeypatch):
    monkeypatch.setattr(retrieval_mod.os, "cpu_count", lambda: 16)
    monkeypatch.setattr(retrieval_mod, "_cgroup_cpu_quota_count", lambda: 2)

    assert retrieval_mod._resolve_tokenize_workers() == 2


def test_feature_pool_chunksize_uses_four_chunks_per_worker():
    assert pipeline_mod._resolve_chunksize(100_000, 2) == 12_500
    assert pipeline_mod._resolve_chunksize(20_000, 2) == 2_500
    assert pipeline_mod._resolve_chunksize(3, 8) == 1


def test_invalid_programmatic_config_fails_closed():
    candidates = _synthetic_candidates(2)

    for config in (
        RankerConfig(scoring_profile="frontier-v55"),
        RankerConfig(bm25_backend="bm25-typo"),
        RankerConfig(top_k=0),
        RankerConfig(max_candidates=0),
        RankerConfig(candidate_pool_size=-1),
        RankerConfig(workers=-1),
    ):
        with pytest.raises(ValueError):
            rank_candidates(candidates, config)


def test_run_ranking_refuses_to_overwrite_candidate_input(tmp_path: Path):
    sample = tmp_path / "sample.json"
    original = "[]\n"
    sample.write_text(original, encoding="utf-8")

    with pytest.raises(ValueError, match="must differ"):
        run_ranking(sample, sample)

    assert sample.read_text(encoding="utf-8") == original


def test_hyre_template_tokens_are_cached():
    hyre_prompts._hyre_token_set.cache_clear()
    jd = "Senior AI/ML Engineer building retrieval systems"
    candidate = "Python engineer who shipped production semantic search"

    first = hyre_prompts.get_hyre_similarity(candidate, jd)
    second = hyre_prompts.get_hyre_similarity(candidate, jd)

    assert first == second
    cache = hyre_prompts._hyre_token_set.cache_info()
    assert cache.misses == 1
    assert cache.hits == 1


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


def test_rank_py_runs_from_repo_without_pythonpath(tmp_path: Path):
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
  }
]
""",
        encoding="utf-8",
    )
    out = tmp_path / "out.csv"
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "rank.py",
            "--candidates",
            str(sample),
            "--out",
            str(out),
            "--top-k",
            "1",
            "--bm25-backend",
            "bm25s",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
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
