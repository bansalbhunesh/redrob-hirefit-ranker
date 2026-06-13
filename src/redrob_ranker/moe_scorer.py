#!/usr/bin/env python3
"""ConFit v2: Role-Aware Mixture of Experts (MMoE) Scorer
Provides a lightweight numpy-based inference engine for the 5 trained role-experts.
"""

import os
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"

# 28 core features + 1 hyre feature = 29 features
INPUT_DIM = 29
HIDDEN_DIM = 64

ROLE_FAMILIES = [
    "AI/ML Engineer",
    "Backend Engineer",
    "DevOps Engineer",
    "Data/BI Engineer",
    "Search Engineer"
]

def detect_role(jd_text: str) -> str:
    """Infers the target role from JD text using keyword heuristics."""
    if not jd_text:
        return "Backend Engineer" # default fallback
        
    text = jd_text.lower()
    
    # Simple scoring logic
    scores = {
        "AI/ML Engineer": ["machine learning", "deep learning", "pytorch", "nlp", "llm", "ai"],
        "Backend Engineer": ["backend", "django", "fastapi", "microservices", "api"],
        "DevOps Engineer": ["kubernetes", "docker", "terraform", "ci/cd", "devops", "sre"],
        "Data/BI Engineer": ["sql", "etl", "snowflake", "redshift", "dbt", "data engineer"],
        "Search Engineer": ["elasticsearch", "opensearch", "solr", "information retrieval", "ranking"]
    }
    
    best_role = "Backend Engineer"
    max_score = 0
    
    for role, keywords in scores.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > max_score:
            max_score = score
            best_role = role
            
    return best_role

class ExpertMLP:
    """A lightweight numpy inference class for a 2-layer MLP."""
    def __init__(self, w1, b1, w2, b2):
        self.w1 = w1
        self.b1 = b1
        self.w2 = w2
        self.b2 = b2
        
    def predict(self, x: np.ndarray) -> np.ndarray:
        # Layer 1 (ReLU)
        h1 = np.maximum(0, x @ self.w1 + self.b1)
        # Layer 2 (Linear)
        out = h1 @ self.w2 + self.b2
        return out

class RoleAwareMoE:
    def __init__(self):
        self.experts = {}
        self._load_experts()
        
    def _load_experts(self):
        if not MODELS_DIR.exists():
            return
            
        for role in ROLE_FAMILIES:
            safe_name = role.replace("/", "_").replace(" ", "_")
            model_path = MODELS_DIR / f"expert_{safe_name}.npz"
            if model_path.exists():
                data = np.load(model_path)
                self.experts[role] = ExpertMLP(
                    w1=data['w1'], b1=data['b1'],
                    w2=data['w2'], b2=data['b2']
                )
                
    def score_candidates(self, jd_text: str, features_matrix: np.ndarray) -> np.ndarray:
        """
        features_matrix: (N, 29) numpy array
        Returns: (N,) numpy array of scores
        """
        role = detect_role(jd_text)
        
        # If model isn't trained yet, return a fallback score
        if role not in self.experts:
            # Fallback to feature 3 (skill_depth) as a proxy
            if features_matrix.shape[1] > 3:
                return features_matrix[:, 3]
            return np.zeros(len(features_matrix))
            
        expert = self.experts[role]
        scores = expert.predict(features_matrix)
        return scores.flatten()

# Global singleton
_moe_instance = None

def get_moe_scorer() -> RoleAwareMoE:
    global _moe_instance
    if _moe_instance is None:
        _moe_instance = RoleAwareMoE()
    return _moe_instance
