"""EXPERIMENTAL dense-embeddings feature: off-path invariance + safe blending.

Uses the dependency-free HashingStubEmbedder so the threading/guardrail logic is
covered without downloading model2vec.
"""
import numpy as np

import redrob_ranker.pipeline as pipeline_mod
from redrob_ranker.embeddings import HashingStubEmbedder, semantic_scores
from redrob_ranker.features import CandidateFeatures, final_score
from redrob_ranker.constants import FEATURE_NAMES
from redrob_ranker.pipeline import RankerConfig, run_ranking


def _features(**vals):
    base = {n: 0.0 for n in FEATURE_NAMES}
    base.update(vals)
    return CandidateFeatures(candidate_id="CAND_0000001", values=base,
                             behavioral_multiplier=1.0, honeypot_multiplier=1.0,
                             disqualifier_multiplier=1.0)


def test_final_score_none_semantic_is_identical_to_default():
    f = _features(core_skill_match=0.8, production_evidence=0.6)
    assert final_score(f, 0.5, None) == final_score(f, 0.5)


def test_semantic_score_changes_total_when_enabled():
    f = _features(core_skill_match=0.8)
    assert final_score(f, 0.5, 1.0) != final_score(f, 0.5, None)
    # a higher semantic score should not decrease the blended base
    assert final_score(f, 0.5, 0.9) >= final_score(f, 0.5, 0.1)


def test_semantic_scores_in_unit_range():
    sims = semantic_scores(["vector search ranking", "marketing brand campaigns"],
                           "retrieval ranking embeddings", HashingStubEmbedder())
    assert set(sims) == {0, 1}
    assert all(0.0 <= v <= 1.0 for v in sims.values())


def test_guardrails_still_suppress_despite_high_semantic():
    honeypot = _features(core_skill_match=1.0)
    honeypot.honeypot_multiplier = 0.0  # hard honeypot
    assert final_score(honeypot, 1.0, 1.0) == 0.0  # semantic cannot rescue it


def test_pipeline_off_path_does_not_import_model2vec(tmp_path, monkeypatch):
    # If embeddings are OFF, constructing the embedder must never happen.
    def _boom(*a, **k):
        raise AssertionError("model2vec must not be touched on the default path")
    monkeypatch.setattr(pipeline_mod, "_PARALLEL_MIN_POOL", 10_000)  # force serial
    import redrob_ranker.embeddings as emb
    monkeypatch.setattr(emb, "StaticModelEmbedder", _boom)
    sample = tmp_path / "s.json"
    sample.write_text(
        '[{"candidate_id":"CAND_0000001","profile":{"current_title":"ML Engineer",'
        '"summary":"shipped ranking","location":"Pune","country":"India",'
        '"years_of_experience":7,"current_company":"CRED","current_industry":"Fintech"},'
        '"career_history":[{"company":"CRED","title":"ML Engineer","duration_months":60,'
        '"is_current":true,"description":"built ranking retrieval"}],"education":[],'
        '"skills":[],"redrob_signals":{"recruiter_response_rate":0.8,'
        '"last_active_date":"2026-05-20","open_to_work_flag":true,"notice_period_days":30}}]',
        encoding="utf-8")
    out = tmp_path / "o.csv"
    res = run_ranking(sample, out, RankerConfig(top_k=1, candidate_pool_size=1, use_embeddings=False))
    assert res.rows[0]["candidate_id"] == "CAND_0000001"


def test_pipeline_on_path_blends_stub_embedder(tmp_path, monkeypatch):
    # With embeddings ON, inject the stub and confirm a valid ranking is produced.
    import redrob_ranker.embeddings as emb
    monkeypatch.setattr(emb, "StaticModelEmbedder", lambda *_a, **_k: HashingStubEmbedder())
    sample = tmp_path / "s.json"
    sample.write_text(
        '[{"candidate_id":"CAND_0000001","profile":{"current_title":"ML Engineer",'
        '"summary":"shipped ranking retrieval","location":"Pune","country":"India",'
        '"years_of_experience":7,"current_company":"CRED","current_industry":"Fintech"},'
        '"career_history":[{"company":"CRED","title":"ML Engineer","duration_months":60,'
        '"is_current":true,"description":"built ranking retrieval"}],"education":[],'
        '"skills":[],"redrob_signals":{"recruiter_response_rate":0.8,'
        '"last_active_date":"2026-05-20","open_to_work_flag":true,"notice_period_days":30}}]',
        encoding="utf-8")
    out = tmp_path / "o.csv"
    res = run_ranking(sample, out, RankerConfig(top_k=1, candidate_pool_size=1, use_embeddings=True))
    assert res.rows[0]["candidate_id"] == "CAND_0000001"
    assert out.read_text(encoding="utf-8").startswith("candidate_id,rank,score,reasoning")
