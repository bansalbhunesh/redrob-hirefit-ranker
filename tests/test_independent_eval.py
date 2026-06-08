"""Tests for the non-circular eval harness."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bil = _load("build_independent_labels")
ev = _load("evaluate_independent")


def _cand(**over):
    c = {
        "candidate_id": "CAND_0000001",
        "profile": {"current_title": "Senior Machine Learning Engineer", "headline": "ranking",
                    "summary": "Shipped production recommendation and retrieval systems at scale",
                    "location": "Pune", "country": "India", "years_of_experience": 7,
                    "current_company": "CRED"},
        "career_history": [{"company": "CRED", "title": "Machine Learning Engineer",
                            "start_date": "2019-01-01", "end_date": None, "duration_months": 60,
                            "is_current": True, "industry": "Fintech",
                            "description": "Built and deployed embeddings retrieval and ranking in production for millions of users"}],
        "skills": [{"name": "FAISS", "proficiency": "advanced", "endorsements": 10, "duration_months": 30}],
        "redrob_signals": {"recruiter_response_rate": 0.8, "last_active_date": "2026-05-20",
                           "open_to_work_flag": True, "notice_period_days": 30},
    }
    c["profile"].update(over.get("profile", {}))
    c.update({k: v for k, v in over.items() if k != "profile"})
    return c


def test_independent_labeler_does_not_import_ranker_features():
    # The whole point: zero shared code with the ranker's feature system.
    # (The docstring may *mention* compute_features; what matters is no import.)
    src = (ROOT / "scripts" / "build_independent_labels.py").read_text(encoding="utf-8")
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            assert "redrob_ranker" not in stripped, f"unexpected ranker import: {stripped}"


def test_strong_candidate_scores_high_tier():
    tier, rel, _ = bil.label_candidate(_cand())
    assert tier >= 4 and rel >= 3.5


def test_non_target_role_with_no_ml_is_tier0():
    c = _cand(profile={"current_title": "Marketing Manager", "summary": "Brand and content marketing leader"},
              career_history=[{"company": "TCS", "title": "Marketing Manager",
                               "start_date": "2018-01-01", "end_date": None,
                               "duration_months": 84, "is_current": True,
                               "description": "content and brand campaigns"}])
    tier, rel, reasons = bil.label_candidate(c)
    assert tier == 0


def test_honeypot_impossible_timeline_is_tier0():
    c = _cand()
    c["profile"]["years_of_experience"] = 8
    c["career_history"][0]["duration_months"] = 200  # exceeds 8*12+30
    tier, rel, reasons = bil.label_candidate(c)
    assert tier == 0 and "honeypot_impossible" in reasons


def test_evaluator_metrics_perfect_and_partial():
    tiers = {"A": 5, "B": 4, "C": 0, "D": 3}
    assert ev.precision_at_k(["A", "B"], tiers, 2) == 1.0
    assert ev.precision_at_k(["C", "A"], tiers, 2) == 0.5
    ap = ev.average_precision(["A", "B", "C", "D"], tiers)
    assert 0.0 < ap <= 1.0
