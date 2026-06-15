"""New INDEPENDENT evidence channels from structured candidate data (the
information-architecture lever, not another model). Three deterministic, offline,
torch-free channels:

  1. BM25F            field-aware lexical scoring (title/skills/career/summary/... kept
                      separate with per-field weights + length norm) vs the flattened bm25.
  2. requirement->evidence  break the JD into atomic requirements + the candidate into
                      evidence units; Hungarian (min-cost) assignment so one vague sentence
                      cannot satisfy every requirement; coverage / weakest-requirement feats.
  3. counterfactual   leave-one-field-out on BM25F -> single-source dependence (a stuffer
                      collapses when its one stuffed field is removed; a real candidate does
                      not, because evidence is corroborated across fields).

All use the shipped tokenizer for consistency. These are scored over the 3000-pool to test
whether FIELD STRUCTURE carries signal INDEPENDENT of the existing flattened features.
"""
from __future__ import annotations

import math
import sys

sys.path.insert(0, "src")
import numpy as np  # noqa: E402

from redrob_ranker.constants import JD_QUERY  # noqa: E402
from redrob_ranker.text import tokenize  # noqa: E402

# ---- field extraction -------------------------------------------------------
FIELD_WEIGHTS = {
    "career_descriptions": 3.0,
    "career_titles": 2.5,
    "verified_skills": 2.0,
    "assessments": 1.8,
    "current_title": 1.5,
    "companies": 1.0,
    "summary": 0.7,
    "headline": 0.5,
}
B = 0.75
K1 = 1.2


def field_texts(cand: dict) -> dict[str, str]:
    p = cand.get("profile") or {}
    career = cand.get("career_history") or []
    skills = cand.get("skills") or []
    sig = cand.get("redrob_signals") or {}
    assess = sig.get("skill_assessment_scores") or {}
    return {
        "career_descriptions": " ".join(str(j.get("description") or "") for j in career),
        "career_titles": " ".join(str(j.get("title") or "") for j in career),
        "verified_skills": " ".join(str(s.get("name") or "") for s in skills),
        "assessments": " ".join(str(k) for k in (assess.keys() if isinstance(assess, dict) else [])),
        "current_title": str(p.get("current_title") or ""),
        "companies": " ".join(str(j.get("company") or "") for j in career) + " " + str(p.get("current_company") or ""),
        "summary": str(p.get("summary") or ""),
        "headline": str(p.get("headline") or ""),
    }


# ---- BM25F ------------------------------------------------------------------
class BM25F:
    def __init__(self, cands: list[dict]):
        self.fields = list(FIELD_WEIGHTS)
        self.toks = []          # per-candidate {field: [tokens]}
        flen = {f: [] for f in self.fields}
        df = {}                 # term -> #candidates containing it (any field)
        for c in cands:
            ft = field_texts(c)
            tk = {f: tokenize(ft[f]) for f in self.fields}
            self.toks.append(tk)
            seen = set()
            for f in self.fields:
                flen[f].append(len(tk[f]))
                for t in tk[f]:
                    if t not in seen:
                        seen.add(t)
            for t in seen:
                df[t] = df.get(t, 0) + 1
        self.N = len(cands)
        self.avg = {f: (sum(flen[f]) / self.N if self.N else 0.0) for f in self.fields}
        self.idf = {t: math.log((self.N - n + 0.5) / (n + 0.5) + 1.0) for t, n in df.items()}
        self.qterms = [t for t in tokenize(JD_QUERY) if t in self.idf]

    def _pseudo_tf(self, tk, drop=None):
        from collections import Counter
        ptf = {}
        for f in self.fields:
            if f == drop:
                continue
            w = FIELD_WEIGHTS[f]
            ln = len(tk[f])
            norm = (1 - B + B * ln / self.avg[f]) if self.avg[f] else 1.0
            for t, c in Counter(tk[f]).items():
                ptf[t] = ptf.get(t, 0.0) + w * c / norm
        return ptf

    def score(self, i, drop=None):
        ptf = self._pseudo_tf(self.toks[i], drop=drop)
        s = 0.0
        for t in self.qterms:
            x = ptf.get(t, 0.0)
            if x:
                s += self.idf[t] * x / (K1 + x)
        return s

    def all_scores(self):
        return np.array([self.score(i) for i in range(self.N)])

    def counterfactual(self):
        """single-source dependence = max field-leave-one-out drop / full score."""
        full = self.all_scores()
        drops = np.zeros((self.N, len(self.fields)))
        for j, f in enumerate(self.fields):
            for i in range(self.N):
                drops[i, j] = full[i] - self.score(i, drop=f)
        denom = np.where(full > 1e-9, full, 1e-9)
        ssd = drops.max(axis=1) / denom          # 1.0 => one field carries everything
        var = drops.var(axis=1)
        return full, ssd, var


# ---- requirement -> evidence assignment ------------------------------------
REQUIREMENTS = {
    "R1_retrieval_prod": ["embedding", "embeddings", "retrieval", "vector", "search", "rag", "semantic", "faiss", "index"],
    "R2_vector_db": ["vector database", "milvus", "qdrant", "pinecone", "weaviate", "hybrid search", "ann"],
    "R3_python_eng": ["python", "pytorch", "tensorflow", "api", "backend", "microservice", "engineering", "pipeline"],
    "R4_ranking_eval": ["ranking", "ranker", "rerank", "ndcg", "mrr", "map", "a/b", "evaluation", "relevance", "learning to rank"],
    "R5_prod_ownership": ["production", "deployed", "shipped", "scale", "millions", "users", "latency", "serving", "throughput"],
    "R6_seniority": ["senior", "lead", "staff", "principal", "architect", "mentor", "ownership"],
    "R7_ml_nlp": ["machine learning", "nlp", "deep learning", "transformer", "llm", "recommendation", "personalization"],
}
MANDATORY = {"R1_retrieval_prod", "R3_python_eng", "R4_ranking_eval", "R5_prod_ownership"}


def _evidence_units(cand: dict) -> list[tuple[str, str, bool]]:
    """(text, source_kind, dated) units. dated=True for dated career entries."""
    units = []
    for j in (cand.get("career_history") or [])[:6]:
        txt = f"{j.get('title') or ''} {j.get('description') or ''} {j.get('company') or ''}"
        dated = bool(j.get("start_date") or j.get("end_date"))
        units.append((txt, "career", dated))
    for s in (cand.get("skills") or [])[:8]:
        if str(s.get("proficiency") or "").lower() in ("expert", "advanced"):
            units.append((str(s.get("name") or ""), "skill", int(s.get("duration_months") or 0) > 0))
    p = cand.get("profile") or {}
    units.append((f"{p.get('current_title') or ''} {p.get('summary') or ''}", "profile", False))
    return [u for u in units if u[0].strip()]


def _match(req_kw: list[str], evid_text: str) -> float:
    low = evid_text.lower()
    hit = sum(1 for kw in req_kw if kw in low)
    return hit / len(req_kw) if req_kw else 0.0


def requirement_features(cand: dict) -> dict[str, float]:
    from scipy.optimize import linear_sum_assignment
    units = _evidence_units(cand)
    reqs = list(REQUIREMENTS)
    if not units:
        return {"req_coverage": 0.0, "req_n_covered": 0.0, "req_weakest_mandatory": 0.0,
                "req_evidence_diversity": 0.0, "req_unsupported": float(len(reqs)),
                "req_avg_conf": 0.0, "req_undated_only": float(len(MANDATORY))}
    M = np.array([[_match(REQUIREMENTS[r], units[e][0]) for e in range(len(units))] for r in reqs])
    # Hungarian: assign each requirement to a DISTINCT evidence unit maximizing match
    ri, ei = linear_sum_assignment(-M)
    assigned = {reqs[r]: (units[e], M[r, e]) for r, e in zip(ri, ei)}
    # also best-evidence per requirement (for weakest-mandatory, not forced-distinct)
    best = {reqs[r]: M[r].max() for r in range(len(reqs))}
    covered = [r for r in reqs if assigned.get(r, (None, 0))[1] >= 0.34]
    used_units = {id(assigned[r][0]) for r in assigned}
    weakest_mand = min(best[r] for r in MANDATORY)
    undated_only = sum(1 for r in MANDATORY
                       if assigned.get(r) and assigned[r][1] >= 0.34 and not assigned[r][0][2])
    return {
        "req_coverage": float(sum(assigned[r][1] for r in assigned)),
        "req_n_covered": float(len(covered)),
        "req_weakest_mandatory": float(weakest_mand),
        "req_evidence_diversity": float(len(used_units)),
        "req_unsupported": float(len(reqs) - len(covered)),
        "req_avg_conf": float(np.mean([assigned[r][1] for r in assigned])),
        "req_undated_only": float(undated_only),
    }
