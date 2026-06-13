#!/usr/bin/env python3
"""
Two-stage learned re-ranker.

Stage 1: Fast lexical scoring (existing BM25 + feature scorer).
Stage 2: LightGBM LambdaMART re-rank on top-300 candidates.

Replaces calibration.py entirely.
"""

from __future__ import annotations

import json
import numpy as np
import lightgbm as lgb
from pathlib import Path
from typing import Dict, List, Tuple

from .features import CandidateFeatures, compute_features

class LearnedReRanker:
    """
    Two-stage ranker: lexical filter + learned re-rank.

    The learned model is trained on pessimistic multiplicative labels,
    so it discovers non-linear interactions that the linear scorer misses.
    """

    FEATURE_NAMES = [
        "bm25_score", "core_skill_match", "nice_skill_match", "skill_depth_score",
        "endorsement_trust", "assessment_score_avg", "github_signal",
        "product_company_ratio", "ir_ranking_experience", "production_evidence",
        "senior_title_held", "career_trajectory_score", "scale_signal",
        "code_writing_recent", "yoe_fit_score", "education_score",
        "ml_ai_tenure_score", "open_source_signal", "location_score",
        "relocation_willing", "notice_period_score", "disqualifier_flag",
        "keyword_stuffer_flag", "consulting_only_flag", "honeypot_multiplier",
        "title_match_score", "backend_depth_score", "data_bi_depth_score",
    ]

    def __init__(self, model_path: str = "reranker_lgbm.txt"):
        self.model = lgb.Booster(model_file=model_path)

    def _features_to_vector(self, features: CandidateFeatures) -> np.ndarray:
        """Convert feature dataclass to numpy vector."""
        return np.array([
            features.values.get("bm25_score", 0.0),
            features.values.get("core_skill_match", 0.0),
            features.values.get("nice_skill_match", 0.0),
            features.values.get("skill_depth_score", 0.0),
            features.values.get("endorsement_trust", 0.0),
            features.values.get("assessment_score_avg", 0.0),
            features.values.get("github_signal", 0.0),
            features.values.get("product_company_ratio", 0.0),
            features.values.get("ir_ranking_experience", 0.0),
            features.values.get("production_evidence", 0.0),
            features.values.get("senior_title_held", 0.0),
            features.values.get("career_trajectory_score", 0.0),
            features.values.get("scale_signal", 0.0),
            features.values.get("code_writing_recent", 0.0),
            features.values.get("yoe_fit_score", 0.0),
            features.values.get("education_score", 0.0),
            features.values.get("ml_ai_tenure_score", 0.0),
            features.values.get("open_source_signal", 0.0),
            features.values.get("location_score", 0.0),
            features.values.get("relocation_willing", 0.0),
            features.values.get("notice_period_score", 0.0),
            1.0 if features.values.get("disqualifier_skill_flag") else 0.0,
            1.0 if features.values.get("keyword_stuffer_flag") else 0.0,
            1.0 if features.values.get("consulting_only_flag") else 0.0,
            features.honeypot_multiplier,
            features.values.get("title_match_score", 0.0),
            features.values.get("backend_depth_score", 0.0),
            features.values.get("data_bi_depth_score", 0.0),
        ], dtype=np.float32)

    def rerank(self, ranked_lexical: List[Tuple[dict, CandidateFeatures, float]]) -> List[Tuple[dict, CandidateFeatures, float]]:
        """
        Two-stage ranking:
        1. Pass in the already-scored candidates from Stage 1.
        2. Re-rank top 300 with learned model.
        3. Return top_k.
        """
        # Re-rank top 300 with learned model. Leave the rest as-is.
        ranked_lexical.sort(key=lambda x: x[2], reverse=True)
        pool = ranked_lexical[:300]
        tail = ranked_lexical[300:]

        # Stage 2: Learned re-ranking
        reranked = []
        for cand, features, lexical_score in pool:

            # Honeypot gate is still absolute (model can't save a trap)
            if features.honeypot_multiplier <= 0.0:
                reranked.append((cand, features, 0.0))
                continue

            # Build feature vector
            vec = self._features_to_vector(features)

            # Predict with LightGBM
            learned_score = float(self.model.predict(vec.reshape(1, -1))[0])

            # Blend: 75% learned, 25% lexical (stability)
            # The learned score is the primary signal; lexical is a safety anchor
            blended_score = 0.75 * learned_score + 0.25 * lexical_score

            # Apply multiplicative behavioral gate (same as current pipeline)
            # In features.py, this is behavioral_multiplier
            if features.behavioral_multiplier > 0:
                blended_score *= features.behavioral_multiplier

            reranked.append((cand, features, blended_score))

        # Sort by final score and append the tail
        reranked.sort(key=lambda x: x[2], reverse=True)
        return reranked + tail
