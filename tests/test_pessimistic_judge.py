"""Unit coverage for the offline pessimistic judge.

`pessimistic_judge.py` is used only by `generate_training_data.py` to synthesize a
harder label distribution; it is OFF the submission path, which is why it carried
0% coverage. The logic is nonetheless pure and deterministic (compute_features +
multiplicative gates, no network), so it is worth pinning against regressions.
"""
from __future__ import annotations

from redrob_ranker.pessimistic_judge import (
    PessimisticJudge,
    PessimisticJudgment,
    batch_judge,
)
from test_features import make_candidate

_GATES = {"honeypot", "title", "role_depth", "production", "behavioral", "skill_core"}


def _hard_honeypot() -> dict:
    """A candidate that trips the zero-tolerance honeypot gate (see test_features)."""
    c = make_candidate()
    c["candidate_id"] = "CAND_HONEYPOT"
    c["career_history"].append(
        {"company": "A", "title": "ML Engineer", "duration_months": 24,
         "is_current": True, "description": "Current role"}
    )
    c["career_history"].append(
        {"company": "B", "title": "Advisor", "duration_months": 12,
         "is_current": True, "description": "Advisory role"}
    )
    c["redrob_signals"]["expected_salary_range_inr_lpa"] = {"min": 40, "max": 20}
    c["education"][0]["start_year"] = 2022
    c["education"][0]["end_year"] = 2020
    c["skills"].append({"name": "FAISS", "proficiency": "expert", "endorsements": 4, "duration_months": 0})
    c["skills"].append({"name": "Milvus", "proficiency": "expert", "endorsements": 4, "duration_months": 0})
    return c


def test_strong_candidate_passes_gates():
    j = PessimisticJudge().judge(make_candidate())
    assert isinstance(j, PessimisticJudgment)
    assert 0.0 < j.score <= 1.0
    assert j.failed_gate is None
    assert set(j.gate_scores) >= _GATES
    assert "honeypot_clean" in j.passed_gates


def test_honeypot_hard_zero_short_circuits():
    j = PessimisticJudge().judge(_hard_honeypot())
    assert j.score == 0.0
    assert j.failed_gate == "honeypot_hard_zero"
    assert j.passed_gates == []
    assert j.gate_scores["honeypot"] <= 0.0


def test_judge_is_deterministic():
    c = make_candidate()
    assert PessimisticJudge().judge(c).score == PessimisticJudge().judge(c).score


def test_role_family_selects_depth_gate():
    c = make_candidate()
    for rf in ("ai_ml_engineering", "backend_engineering", "data_bi_analytics",
               "devops_cloud", "search_relevance"):
        j = PessimisticJudge(role_family=rf).judge(c)
        assert isinstance(j, PessimisticJudgment)
        assert 0.0 <= j.score <= 1.0
        assert any(g.startswith("role_depth") for g in j.passed_gates)


def test_weak_title_is_penalized_but_scored():
    weak = make_candidate()
    weak["profile"]["current_title"] = "Marketing Manager"
    weak["career_history"][0]["title"] = "Marketing Manager"
    weak["career_history"][0]["description"] = "Used ChatGPT for content marketing."
    strong = PessimisticJudge().judge(make_candidate())
    j = PessimisticJudge().judge(weak)
    assert 0.0 <= j.score <= 1.0
    assert j.score < strong.score


def test_batch_judge_matches_input_length():
    out = batch_judge([make_candidate(), _hard_honeypot()])
    assert len(out) == 2
    assert all(isinstance(j, PessimisticJudgment) for j in out)
    assert out[1].score == 0.0
