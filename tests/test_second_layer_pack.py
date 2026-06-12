from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _candidate(
    cid: str,
    *,
    title: str,
    skills: list[str],
    description: str,
    yoe: float = 6.0,
    open_to_work: bool = True,
) -> dict:
    return {
        "candidate_id": cid,
        "profile": {
            "current_title": title,
            "headline": title,
            "summary": description,
            "location": "Bangalore",
            "country": "India",
            "years_of_experience": yoe,
            "current_company": "Razorpay",
        },
        "skills": [
            {
                "name": skill,
                "proficiency": "advanced",
                "duration_months": 36,
                "endorsements": 5,
            }
            for skill in skills
        ],
        "career_history": [
            {
                "company": "Razorpay",
                "title": title,
                "description": description,
                "duration_months": int(yoe * 12),
                "is_current": True,
            }
        ],
        "redrob_signals": {
            "open_to_work_flag": open_to_work,
            "notice_period_days": 30,
            "recruiter_response_rate": 0.72 if open_to_work else 0.05,
            "last_active_date": "2026-06-01",
            "profile_completeness_score": 90,
            "verified_email": True,
            "verified_phone": True,
        },
    }


def test_second_layer_generator_outputs_label_free_annotation_pack(tmp_path):
    candidates = [
        _candidate(
            "CAND_AI",
            title="Senior AI Engineer",
            skills=["Python", "Embeddings", "Vector Search", "RAG", "NDCG", "PyTorch"],
            description="Shipped production retrieval ranking and vector search systems at scale.",
        ),
        _candidate(
            "CAND_BACKEND",
            title="Senior Backend Engineer",
            skills=["Java", "Microservices", "Kafka", "Redis", "PostgreSQL", "Docker"],
            description="Built production APIs, microservices and distributed platform services.",
        ),
        _candidate(
            "CAND_DEVOPS",
            title="DevOps Engineer",
            skills=["Kubernetes", "Docker", "Terraform", "AWS", "Prometheus", "Grafana"],
            description="Owned production reliability, CI/CD, monitoring and cloud infrastructure.",
        ),
        _candidate(
            "CAND_DATA",
            title="Senior Data Analyst",
            skills=["SQL", "Power BI", "ETL", "Snowflake", "Dashboard", "Data Modeling"],
            description="Built warehouse models, dashboards, metrics and stakeholder reporting.",
        ),
        _candidate(
            "CAND_TRAP",
            title="Marketing Manager",
            skills=["Embeddings", "Vector Search", "Pinecone", "RAG", "Prompt Engineering"],
            description="Marketing profile listing AI buzzwords without delivery evidence.",
            open_to_work=False,
        ),
    ]
    candidate_path = tmp_path / "candidates.jsonl"
    with candidate_path.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate) + "\n")

    manifest = tmp_path / "download_manifest.json"
    manifest.write_text(
        json.dumps({
            "records": [
                {
                    "kind": "huggingface_dataset",
                    "source": "netsol/resume-score-details",
                    "file": "README.md",
                    "bytes": 10,
                }
            ]
        }),
        encoding="utf-8",
    )
    out_dir = tmp_path / "second_layer"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_second_layer_pack.py",
            "--candidates",
            str(candidate_path),
            "--external-manifest",
            str(manifest),
            "--out-dir",
            str(out_dir),
            "--sample-size",
            "5",
            "--pair-count",
            "6",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

    expected = {
        "blind_annotation_pack.jsonl",
        "annotation_sampling_key.jsonl",
        "proxy_labels.jsonl",
        "pairwise_proxy_labels.jsonl",
        "hard_negative_proxy.jsonl",
        "role_family_rubrics.json",
        "external_dataset_inventory.json",
        "no_peeking_eval_protocol.json",
        "second_layer_summary.json",
        "README.md",
    }
    assert expected <= {p.name for p in out_dir.iterdir()}
    assert not (out_dir / "submission.csv").exists()

    blind = [
        json.loads(line)
        for line in (out_dir / "blind_annotation_pack.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert blind
    assert all("label" not in row for row in blind)
    assert all("relevance" not in row for row in blind)
    assert all("component_scores" not in row for row in blind)
    assert all("candidate_summary" in row for row in blind)

    proxy = [
        json.loads(line)
        for line in (out_dir / "proxy_labels.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert proxy
    assert all(row["judge_type"] == "deterministic_proxy_rubric_not_blind" for row in proxy)
    assert {row["role_family"] for row in proxy} & {
        "ai_ml_engineering",
        "backend_engineering",
        "devops_cloud",
        "data_bi_analytics",
    }

    protocol = json.loads((out_dir / "no_peeking_eval_protocol.json").read_text(encoding="utf-8"))
    assert any("never send proxy_labels" in rule.lower() for rule in protocol["rules"])

    summary = json.loads((out_dir / "second_layer_summary.json").read_text(encoding="utf-8"))
    assert summary["counts"]["blind_annotation_pack_rows"] == len(blind)
    assert summary["external_inventory"]["source_count"] == 1
