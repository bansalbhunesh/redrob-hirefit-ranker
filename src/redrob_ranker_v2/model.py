"""The v2 learned ranker.

Architecture
------------
score(candidate) = normalize( learned_relevance(features) ) * integrity_gate

* ``learned_relevance`` is a LightGBM LambdaMART model (objective ``lambdarank``,
  the metric the challenge actually scores on is NDCG, so we optimize NDCG
  directly). When no trained model file is present, a transparent linear
  fallback keeps the pipeline runnable offline so plumbing can be validated
  without the (large, gitignored) candidate pool.
* ``integrity_gate`` = honeypot_multiplier * disqualifier_multiplier, applied
  *after* the learned score. This is deliberately outside the learned model so
  the challenge's hard rules hold no matter what the model learns: a honeypot or
  disqualified profile cannot be promoted into the top-100 by the ranker. This
  is what keeps the "honeypot rate in top-100 <= 10%" disqualifier safe.

The feature vector is the 33 extracted features (shared extractor) plus the
normalized BM25 retrieval score — 34 columns, fixed order in ``V2_FEATURES``.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from redrob_ranker.constants import FEATURE_NAMES

# Fixed feature order the model trains and scores on. Retrieval score is appended
# so the learned ranker can weigh lexical match alongside the structured signals.
V2_FEATURES: tuple[str, ...] = tuple(FEATURE_NAMES) + ("bm25_score",)

# Default model location (LightGBM text dump). Trained by redrob_ranker_v2.train.
DEFAULT_MODEL_PATH = Path(
    os.environ.get("REDROB_V2_MODEL", Path(__file__).resolve().parents[2] / "models" / "ltr_v2.txt")
)

# Transparent linear fallback used ONLY when no trained model is present. These
# weights are independent of the old pipeline's BASE_FEATURE_WEIGHTS; they encode
# the JD's stated priorities (shipped retrieval/ranking in production > generic
# skills; seniority band; reachable) so blind runs are sensible, not random. The
# trained LambdaMART model replaces this entirely.
_FALLBACK_WEIGHTS: dict[str, float] = {
    "production_evidence": 0.16,
    "ir_ranking_experience": 0.15,
    "core_skill_match": 0.12,
    "hyre_similarity": 0.08,
    "title_match_score": 0.07,
    "career_trajectory_score": 0.06,
    "bm25_score": 0.06,
    "yoe_fit_score": 0.05,
    "ml_ai_tenure_score": 0.05,
    "product_company_ratio": 0.05,
    "skill_depth_score": 0.04,
    "scale_signal": 0.03,
    "code_writing_recent": 0.03,
    "responsiveness_score": 0.02,
    "availability_score": 0.02,
    "location_score": 0.01,
}


class LearnedRanker:
    """LightGBM LambdaMART ranker with a principled linear fallback."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = Path(model_path) if model_path is not None else DEFAULT_MODEL_PATH
        self.booster = None
        self.kind = "fallback-linear"
        if self.model_path.exists():
            import lightgbm as lgb

            self.booster = lgb.Booster(model_file=str(self.model_path))
            self.kind = "lightgbm-lambdamart"

    def _fallback_scores(self, X: np.ndarray) -> np.ndarray:
        idx = {name: i for i, name in enumerate(V2_FEATURES)}
        out = np.zeros(X.shape[0], dtype=np.float64)
        for name, w in _FALLBACK_WEIGHTS.items():
            out += w * X[:, idx[name]]
        return out

    def relevance(self, X: np.ndarray) -> np.ndarray:
        """Raw learned relevance (higher = better), one score per row."""
        if self.booster is not None:
            return np.asarray(self.booster.predict(X), dtype=np.float64)
        return self._fallback_scores(X)

    def score(self, X: np.ndarray, gates: np.ndarray) -> np.ndarray:
        """Final ranking score in [0, 1]: min-max-normalized relevance * gate.

        Normalization makes the learned relevance non-negative so the
        multiplicative integrity gate demotes (never accidentally promotes via a
        sign flip) honeypots and disqualified profiles. Pure ranking is
        scale-invariant, so this does not distort order within the un-gated set.
        """
        rel = self.relevance(X)
        lo, hi = float(rel.min()), float(rel.max())
        norm = (rel - lo) / (hi - lo) if hi > lo else np.zeros_like(rel)
        return norm * gates
