"""Probe JD compiler generalization on representative role descriptions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.jd_compiler import compile_jd


JDS = {
    "senior_ai_engineer": """
Senior AI Engineer, 5-9 years. Build production LLM, retrieval, embeddings,
vector database, ranking and evaluation systems in Python. Location India.
""",
    "backend_platform_engineer": """
Senior Backend Engineer, 4-8 years. Own Python APIs, Kafka distributed systems,
Spark data processing and internal search relevance. Bangalore or Chennai.
""",
    "search_relevance_engineer": """
Search Relevance Engineer, 5-8 years. Improve ranking, re-rank, information
retrieval, Elasticsearch/OpenSearch and offline NDCG/MRR evaluation.
""",
    "unsupported_sales_manager": """
Sales Manager, 6-10 years. Own enterprise pipeline, account plans, negotiation,
CRM hygiene and quarterly revenue forecasting.
""",
}


def probe() -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for name, text in JDS.items():
        try:
            compiled = compile_jd(text, source=name)
        except ValueError as exc:
            results[name] = {"status": "unsupported", "error": str(exc)}
            continue
        results[name] = {
            "status": "compiled",
            "must_groups": [group for group, _ in compiled.must_have_skills],
            "nice_groups": [group for group, _ in compiled.nice_to_have_skills],
            "title_family_top": list(compiled.target_title_weights_dict())[:5],
            "locations": list(compiled.preferred_locations)[:8],
            "yoe_target": compiled.yoe_target,
            "query_preview": compiled.jd_query[:180],
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe JD compiler generalization.")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    payload = json.dumps(probe(), indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
