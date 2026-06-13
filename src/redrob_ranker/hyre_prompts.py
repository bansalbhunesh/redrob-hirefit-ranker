# Hypothetical Resume Embeddings (HyRE) for ConFit v2
#
# NAMING NOTE: the runtime feature `hyre_similarity` (see get_hyre_similarity
# below) is a LEXICAL Jaccard overlap between the candidate text and the role
# template — it does NOT use neural embeddings at inference time. The committed
# `artifacts/hyre_embeddings.json` (produced offline by scripts/hyre_generate.py)
# is retained only for offline analysis/experiments and is read on no ranking path.

HYRE_PROMPTS = {
    "AI/ML Engineer": """
    Senior AI/ML Engineer with 6+ years of experience building and deploying scalable machine learning models.
    Expert in PyTorch, TensorFlow, and HuggingFace.
    Strong background in natural language processing (NLP), large language models (LLMs), and retrieval-augmented generation (RAG).
    Production experience serving models with FastAPI, ONNX, and TensorRT on AWS/GCP.
    Deep understanding of vector databases (Pinecone, Milvus, Qdrant) and semantic search architectures.
    Track record of publishing research or contributing to open-source ML projects.
    """,
    "Backend Engineer": """
    Senior Backend Engineer with 8+ years of experience designing high-throughput, low-latency distributed systems.
    Expert in Go, Java, Python, and C++.
    Deep expertise in microservices architecture, gRPC, REST APIs, and event-driven systems (Kafka, RabbitMQ).
    Strong database skills including PostgreSQL, MySQL, Redis, and Cassandra at petabyte scale.
    Experience with cloud-native infrastructure, Kubernetes, Docker, and CI/CD pipelines.
    Proven ability to optimize system performance, handle concurrency, and ensure 99.99% uptime.
    """,
    "Data/BI Engineer": """
    Senior Data Engineer / BI Developer with 7+ years of experience building scalable data pipelines and analytics platforms.
    Expert in SQL, Python, Scala, and PySpark.
    Deep experience with modern data stack tools: Snowflake, BigQuery, dbt, Airflow, and Fivetran.
    Strong background in data modeling, ETL/ELT architecture, and streaming data (Kafka, Flink).
    Proficient in data visualization and business intelligence tools like Tableau, Looker, or PowerBI.
    Track record of delivering actionable insights and driving data-informed business decisions.
    """,
    "DevOps/SRE": """
    Senior Site Reliability Engineer / DevOps with 7+ years of experience managing global cloud infrastructure.
    Expert in AWS, GCP, Azure, and infrastructure as code (Terraform, CloudFormation).
    Deep expertise in container orchestration (Kubernetes, EKS, GKE) and CI/CD (GitHub Actions, Jenkins, GitLab).
    Strong scripting skills in Python, Go, and Bash.
    Experience with monitoring and observability tools (Datadog, Prometheus, Grafana, ELK stack).
    Proven track record of implementing zero-downtime deployments, auto-scaling, and incident response.
    """,
    "Search/Ranking": """
    Senior Search and Ranking Engineer with 6+ years of experience building scalable search engines and recommendation systems.
    Expert in Elasticsearch, Solr, OpenSearch, and Lucene internals.
    Deep background in Information Retrieval (IR), BM25, TF-IDF, and learning-to-rank (LTR) algorithms.
    Experience with e-commerce product search, query understanding, spell correction, and autocomplete.
    Strong ML skills applied to personalization, collaborative filtering, and two-tower neural retrieval models.
    Proficient in Java, Python, and C++ for high-performance retrieval systems.
    """
}

def get_hyre_for_role(role_name: str) -> str:
    """Returns the hypothetical perfect resume for the given role family."""
    for key, text in HYRE_PROMPTS.items():
        if key.split("/")[0].lower() in role_name.lower() or key.lower() in role_name.lower():
            return text.strip()
    return HYRE_PROMPTS["AI/ML Engineer"].strip()

def get_hyre_similarity(candidate_text: str, jd_text: str) -> float:
    """
    Computes a fast lexical Jaccard similarity between the candidate's text
    and the HyRE template corresponding to the JD's role.
    """
    if not candidate_text:
        return 0.0
        
    hyre_text = get_hyre_for_role(jd_text)
    
    # Simple normalization and tokenization
    cand_tokens = set(candidate_text.lower().replace(",", " ").replace(".", " ").split())
    hyre_tokens = set(hyre_text.lower().replace(",", " ").replace(".", " ").split())
    
    if not cand_tokens or not hyre_tokens:
        return 0.0
        
    intersection = cand_tokens.intersection(hyre_tokens)
    union = cand_tokens.union(hyre_tokens)
    
    # Jaccard similarity
    return len(intersection) / len(union)
