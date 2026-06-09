"""Optional dense-retrieval signal (EXPERIMENTAL, opt-in, default OFF).

Design note (why this is a *feature*, not a ranker)
---------------------------------------------------
On this dataset the traps are buzzword-dense profiles (keyword stuffers) and
impossible honeypots. A raw cosine-similarity ranker rewards exactly those - it
sees a stuffer as "semantically very AI". So dense similarity enters the system as
ONE additive feature inside the existing matrix, and the multiplicative behavioral
/ honeypot / disqualifier guardrails still apply on top. Embeddings widen recall
and add soft semantic fit; they never override the structured recruiter logic.

The official ranking path does NOT import or run this unless `--use-embeddings` is
passed. Model weights are a precomputed local artifact (spec section 10.3); no
network call happens during ranking. model2vec/potion is a static embedder
(token-vector lookup + mean pool), so it is CPU-only and fast.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray:  # pragma: no cover - interface
        ...


class StaticModelEmbedder:
    """Wraps a model2vec StaticModel (e.g. minishlab/potion-retrieval-32M).

    Imported lazily so the package has zero hard dependency on model2vec; the
    official ranking path never constructs this.
    """

    def __init__(self, model_name: str = "minishlab/potion-retrieval-32M"):
        try:
            from model2vec import StaticModel
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError(
                "model2vec is not installed. It has no Python 3.14 wheel yet; run the "
                "embedding experiment in the 3.11 Docker image / venv: pip install model2vec"
            ) from exc
        self._model = StaticModel.from_pretrained(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self._model.encode(texts), dtype=np.float32)


class HashingStubEmbedder:
    """Deterministic, dependency-free stub for tests and CI.

    Not semantically meaningful - it only lets the blending/threading logic be
    exercised without downloading a model. Never use it for a real run.
    """

    def __init__(self, dim: int = 64):
        self.dim = dim

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for tok in str(t).lower().split():
                out[i, (hash(tok) % self.dim)] += 1.0
        return out


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def semantic_scores(
    candidate_texts: list[str], jd_text: str, embedder: Embedder
) -> dict[int, float]:
    """Return {candidate_index: cosine(JD, candidate) in [0,1]} as a recall signal."""
    if not candidate_texts:
        return {}
    cand = _l2_normalize(embedder.encode(candidate_texts))
    jd = _l2_normalize(embedder.encode([jd_text]))[0]
    sims = cand @ jd  # cosine, since both are L2-normalized
    sims = (sims + 1.0) / 2.0  # map [-1,1] -> [0,1]
    return {int(i): float(s) for i, s in enumerate(sims)}
