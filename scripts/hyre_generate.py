#!/usr/bin/env python3
"""ConFit v2 HyRE: Hypothetical Resume Embedding
Generates 5 perfect role-family resumes and encodes them.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Please install sentence-transformers: pip install sentence-transformers")
    sys.exit(1)


HYRE_TEMPLATES = {
    "AI/ML Engineer": """
    Senior AI/ML Engineer with 8 years of experience.
    Expert in designing and deploying production Machine Learning, Deep Learning, and NLP models.
    Built scalable LLM pipelines using PyTorch, Transformers, and HuggingFace.
    Strong software engineering fundamentals in Python, C++, and CUDA.
    Deployed models serving millions of requests via FastAPI and TorchServe on Kubernetes.
    Led end-to-end model training, fine-tuning, and MLOps deployment on AWS/GCP.
    """,
    "Backend Engineer": """
    Senior Backend Software Engineer with 8+ years of experience.
    Expert in Python, Django, FastAPI, and Go.
    Designed and built highly scalable, low-latency microservices architecture.
    Deep knowledge of RDBMS (PostgreSQL, MySQL), NoSQL (MongoDB, Redis), and message brokers (Kafka, RabbitMQ).
    Strong track record of optimizing database queries, improving API latency, and handling high-throughput distributed systems.
    Deployed robust backend infrastructure on AWS using Kubernetes, Docker, and CI/CD pipelines.
    """,
    "DevOps Engineer": """
    Senior DevOps/SRE Engineer with 8 years of experience.
    Specialized in infrastructure as code (Terraform, Ansible) and container orchestration (Kubernetes, Docker).
    Expert in CI/CD pipeline automation (Jenkins, GitHub Actions, GitLab CI).
    Strong background in cloud architecture (AWS, GCP, Azure) and multi-region deployments.
    Implemented comprehensive monitoring and alerting with Prometheus, Grafana, ELK stack, and Datadog.
    Maintained 99.99% uptime for production systems with rapid incident response and auto-scaling setups.
    """,
    "Data/BI Engineer": """
    Senior Data/BI Engineer with 8+ years of experience.
    Expert in building scalable ETL/ELT pipelines and data warehouses (Snowflake, Redshift, BigQuery).
    Advanced proficiency in SQL, Python, and PySpark for big data processing.
    Extensive experience with data modeling, dbt, and Apache Airflow orchestration.
    Built comprehensive BI dashboards (Tableau, Looker, PowerBI) for executive stakeholders.
    Optimized query performance and reduced data pipeline latency by 80%.
    """,
    "Search Engineer": """
    Senior Search/Ranking Engineer with 8 years of experience.
    Expert in Information Retrieval, Search Relevance, and ranking algorithms.
    Built large-scale search infrastructure using Elasticsearch, OpenSearch, Solr, and Lucene.
    Implemented Learning to Rank (LTR), vector search, and hybrid BM25 + semantic retrieval systems.
    Experience with Qdrant, FAISS, and dense embedding retrieval.
    Optimized search latency and improved NDCG metrics for enterprise-scale e-commerce platforms.
    """
}

def main():
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Encoding HyRE templates...")
    roles = list(HYRE_TEMPLATES.keys())
    texts = [HYRE_TEMPLATES[r] for r in roles]
    
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    
    out_dict = {}
    for i, role in enumerate(roles):
        out_dict[role] = embeddings[i].tolist()
        
    out_path = ROOT / "artifacts" / "hyre_embeddings.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, indent=2)
        
    print(f"Saved HyRE embeddings to {out_path}")

if __name__ == "__main__":
    main()
