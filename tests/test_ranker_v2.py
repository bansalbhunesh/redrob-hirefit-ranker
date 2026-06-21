"""Smoke + contract tests for the v2 learned ranker (fallback model)."""

from __future__ import annotations

import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker_v2.pipeline_v2 import run_ranking_v2  # noqa: E402
from redrob_ranker_v2.model import LearnedRanker, V2_FEATURES  # noqa: E402


def _sample_path() -> Path:
    return ROOT / "demo_sample.jsonl"


def test_feature_vector_width():
    # 33 shared features + bm25
    assert len(V2_FEATURES) == 34
    assert V2_FEATURES[-1] == "bm25_score"


def test_v2_runs_and_is_valid(tmp_path: Path):
    out = tmp_path / "sub.csv"
    res = run_ranking_v2(_sample_path(), out, top_k=20)
    assert res.model_kind == "fallback-linear"  # no trained model in CI
    assert len(res.rows) == 20
    # ranks are 1..20 unique, scores non-increasing
    ranks = [r["rank"] for r in res.rows]
    assert ranks == list(range(1, 21))
    scores = [float(r["score"]) for r in res.rows]
    assert all(a >= b for a, b in zip(scores, scores[1:]))
    # every reasoning is non-empty
    assert all(r["reasoning"].strip() for r in res.rows)


def test_v2_deterministic(tmp_path: Path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    run_ranking_v2(_sample_path(), a, top_k=20)
    run_ranking_v2(_sample_path(), b, top_k=20)
    assert a.read_text() == b.read_text()


def test_gate_demotes_honeypot(tmp_path: Path):
    import numpy as np

    ranker = LearnedRanker()
    X = np.ones((2, len(V2_FEATURES)))
    gates = np.array([1.0, 0.0])  # second row fully gated (honeypot)
    scores = ranker.score(X, gates)
    assert scores[1] == 0.0
    assert scores[0] >= scores[1]
