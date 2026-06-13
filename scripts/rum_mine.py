#!/usr/bin/env python3
"""ConFit v2 RUM: Hard Negative Mining
Extracts 200-400 hard negatives from the top 3-4% similarity zone
against 5 role-family JDs.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.io import iter_candidates
from redrob_ranker.features import compute_features

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Please install sentence-transformers: pip install sentence-transformers")
    sys.exit(1)


ROLE_FAMILIES = {
    "AI/ML Engineer": "Senior AI/ML Engineer. Requirements: Machine Learning, Deep Learning, PyTorch, Transformers, LLMs, NLP, Python. Must have production deployment experience.",
    "Backend Engineer": "Senior Backend Software Engineer. Requirements: Python, Django/FastAPI, microservices, system design, PostgreSQL, Redis, AWS.",
    "DevOps Engineer": "Senior DevOps/SRE Engineer. Requirements: Kubernetes, Docker, Terraform, CI/CD, AWS/GCP, infrastructure as code, monitoring.",
    "Data/BI Engineer": "Senior Data/BI Engineer. Requirements: SQL, ETL pipelines, Snowflake/Redshift, dbt, Apache Airflow, data warehousing.",
    "Search Engineer": "Senior Search/Ranking Engineer. Requirements: Elasticsearch, OpenSearch, Solr, Information Retrieval, ranking algorithms, Lucene."
}

def main():
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Encoding JDs...")
    jd_names = list(ROLE_FAMILIES.keys())
    jd_texts = [ROLE_FAMILIES[name] for name in jd_names]
    jd_embeddings = model.encode(jd_texts, convert_to_numpy=True, normalize_embeddings=True)
    
    cands_path = ROOT / "candidates.jsonl"
    print(f"Loading candidates from {cands_path}...")
    
    candidates = []
    features_list = []
    texts = []
    
    # Process in chunks to avoid massive memory spike
    for i, c in enumerate(iter_candidates(cands_path)):
        candidates.append(c)
        feats = compute_features(c)
        features_list.append(feats)
        
        # Build document text
        exp_texts = []
        for exp in c.get("experience", []):
            if "title" in exp:
                exp_texts.append(exp["title"])
            if "description" in exp:
                exp_texts.append(exp["description"])
        
        skills = []
        for s in c.get("skills", []):
            if isinstance(s, dict) and "name" in s:
                skills.append(s["name"])
            elif isinstance(s, str):
                skills.append(s)
                
        text = str(c.get("summary", "")) + " " + " ".join(exp_texts) + " " + " ".join(skills)
        texts.append(text[:2000]) # Cap text length for speed
        
        if (i + 1) % 10000 == 0:
            print(f"Loaded {i + 1} candidates...")
            
    print(f"Total candidates: {len(texts)}. Encoding...")
    
    # Batch encode
    cand_embeddings = model.encode(
        texts,
        batch_size=256,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    # Compute cosine similarities (cand_embeddings @ jd_embeddings.T)
    # Shape: (N_candidates, 5)
    similarities = cand_embeddings @ jd_embeddings.T
    
    # We want top 3-4% overall similarity. 
    # For each candidate, get their max similarity across the 5 JDs.
    max_sims = np.max(similarities, axis=1)
    
    # Find the threshold for top 4% and top 3%
    p96 = np.percentile(max_sims, 96)
    p97 = np.percentile(max_sims, 97)
    
    print(f"Similarity thresholds: Top 4% > {p96:.4f}, Top 3% > {p97:.4f}")
    
    hard_negatives = []
    
    for i in range(len(candidates)):
        sim = max_sims[i]
        # In the 3-4% zone
        if p96 <= sim <= p97:
            feats = features_list[i]
            
            # Check if it's a trap
            is_trap = False
            trap_reasons = []
            
            if feats.honeypot_multiplier < 1.0:
                is_trap = True
                trap_reasons.append("honeypot")
            if feats.values.get("keyword_stuffer_flag", 0) > 0:
                is_trap = True
                trap_reasons.append("keyword_stuffer")
            if feats.values.get("disqualifier_skill_flag", 0) > 0:
                is_trap = True
                trap_reasons.append("disqualifier")
                
            # If the depth is extremely low despite high similarity
            # Assuming AI is the matched role (just an approximation)
            matched_jd_idx = np.argmax(similarities[i])
            matched_role = jd_names[matched_jd_idx]
            
            if matched_role == "AI/ML Engineer" and feats.values.get("ai_depth_score", feats.values.get("skill_depth_score", 0)) < 0.2:
                is_trap = True
                trap_reasons.append("low_depth")
                
            if is_trap:
                cand = candidates[i]
                cand["rum_similarity"] = float(sim)
                cand["rum_matched_role"] = matched_role
                cand["rum_trap_reasons"] = trap_reasons
                hard_negatives.append(cand)
                
    print(f"Mined {len(hard_negatives)} hard negatives.")
    
    out_path = ROOT / "rum_hard_negatives.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for cand in hard_negatives:
            f.write(json.dumps(cand) + "\n")
            
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
