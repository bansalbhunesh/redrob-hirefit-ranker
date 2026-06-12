#!/usr/bin/env python3
"""Mine backend and data/BI depth-term evidence from downloaded public datasets.

This does not train the ranker and does not touch the frozen Redrob submission.
It scans the local ignored ``data/external`` corpus, counts role-specific terms
inside rows that look backend/data related, and writes a small provenance report
for the deterministic depth lexicons used by the lab branch.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
TOKEN_RE = re.compile(r"[a-z0-9+#.]{2,}")

ROLE_TERMS: dict[str, dict[str, tuple[str, ...]]] = {
    "backend_platform": {
        "seeds": (
            "backend engineer", "software engineer", "java developer", "platform engineer",
            "api", "microservices", "distributed systems", "spring boot",
        ),
        "api": (
            "rest api", "api gateway", "graphql", "grpc", "websocket", "microservices",
            "spring boot", "fastapi", "flask", "django", "nodejs",
        ),
        "database_cache": (
            "postgres", "postgresql", "mysql", "mongodb", "cassandra", "dynamodb",
            "redis", "kafka", "rabbitmq", "sql", "database", "caching",
        ),
        "scale_reliability": (
            "qps", "rps", "p99", "p95", "latency", "throughput", "scale",
            "high availability", "fault tolerant", "load balancing", "rate limiting",
        ),
        "infra": (
            "docker", "kubernetes", "terraform", "aws", "azure", "gcp",
            "ci/cd", "jenkins", "github actions", "deployment",
        ),
    },
    "data_bi": {
        "seeds": (
            "data analyst", "business intelligence", "analytics engineer", "data engineer",
            "dashboard", "power bi", "tableau", "etl", "data warehouse",
        ),
        "sql": (
            "sql", "window function", "cte", "partition by", "query optimization",
            "stored procedure", "index tuning",
        ),
        "warehouse": (
            "data warehouse", "snowflake", "bigquery", "redshift", "databricks",
            "star schema", "fact table", "dimension table", "dbt",
        ),
        "visualization": (
            "tableau", "power bi", "looker", "metabase", "superset", "dashboard",
            "reporting", "kpi", "metrics",
        ),
        "etl_quality": (
            "etl", "elt", "data pipeline", "airflow", "prefect", "dagster",
            "scheduled refresh", "data quality", "data model", "data modeling",
        ),
        "business_impact": (
            "stakeholders", "business users", "executives", "saved", "automated reporting",
            "decision", "revenue", "cost reduction", "self service", "adoption",
        ),
    },
}


def norm(text: object) -> str:
    return " ".join(match.group(0) for match in TOKEN_RE.finditer(str(text or "").lower()))


def has_term(blob: str, term: str) -> bool:
    term_n = norm(term)
    if not term_n:
        return False
    if " " in term_n:
        return term_n in blob
    return f" {term_n} " in f" {blob} "


def csv_files(external_dir: Path, max_file_mb: float) -> Iterable[Path]:
    for path in sorted(external_dir.rglob("*.csv")):
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
        except OSError:
            continue
        if size_mb <= max_file_mb:
            yield path


def scan_csv(path: Path, max_rows: int) -> Iterable[str]:
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            if idx >= max_rows:
                return
            yield norm(" ".join(str(value or "") for value in row.values()))


def mine(external_dir: Path, max_rows_per_file: int, max_file_mb: float) -> dict:
    role_counts: dict[str, dict[str, Counter[str]]] = {
        role: {category: Counter() for category in categories if category != "seeds"}
        for role, categories in ROLE_TERMS.items()
    }
    role_rows: dict[str, int] = defaultdict(int)
    file_rows: list[dict] = []

    for path in csv_files(external_dir, max_file_mb=max_file_mb):
        local_rows = 0
        local_role_hits = Counter()
        for blob in scan_csv(path, max_rows=max_rows_per_file):
            local_rows += 1
            for role, categories in ROLE_TERMS.items():
                if not any(has_term(blob, seed) for seed in categories["seeds"]):
                    continue
                role_rows[role] += 1
                local_role_hits[role] += 1
                for category, terms in categories.items():
                    if category == "seeds":
                        continue
                    for term in terms:
                        if has_term(blob, term):
                            role_counts[role][category][term] += 1
        if local_rows:
            file_rows.append({
                "path": str(path.relative_to(external_dir)),
                "rows_scanned": local_rows,
                "role_hits": dict(local_role_hits),
            })

    return {
        "external_dir": str(external_dir),
        "max_rows_per_file": max_rows_per_file,
        "max_file_mb": max_file_mb,
        "role_rows": dict(role_rows),
        "files": file_rows,
        "term_counts": {
            role: {
                category: dict(counter.most_common())
                for category, counter in categories.items()
            }
            for role, categories in role_counts.items()
        },
    }


def write_markdown(path: Path, result: dict) -> None:
    lines = [
        "# External Role-Depth Term Mining",
        "",
        "This report scans the locally downloaded public recruiting/resume datasets.",
        "It is provenance for deterministic backend and data/BI depth lexicons; it is not hidden-label evidence.",
        "",
        f"- External dir: `{result['external_dir']}`",
        f"- Max rows per CSV: `{result['max_rows_per_file']}`",
        f"- Max CSV size: `{result['max_file_mb']} MB`",
        "",
        "## Role Rows",
        "",
    ]
    for role, count in sorted(result["role_rows"].items()):
        lines.append(f"- `{role}`: {count:,} matched rows")
    lines.extend(["", "## Top Terms", ""])
    for role, categories in result["term_counts"].items():
        lines.extend([f"### {role}", ""])
        for category, counts in categories.items():
            top = list(counts.items())[:12]
            rendered = ", ".join(f"`{term}` {count}" for term, count in top) or "none"
            lines.append(f"- `{category}`: {rendered}")
        lines.append("")
    lines.extend(["## Files Scanned", ""])
    for item in result["files"]:
        hits = ", ".join(f"{role}={count}" for role, count in sorted(item["role_hits"].items())) or "no role hits"
        lines.append(f"- `{item['path']}`: {item['rows_scanned']:,} rows; {hits}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-dir", type=Path, default=ROOT / "data" / "external")
    parser.add_argument("--out-json", type=Path, default=ROOT / "artifacts" / "external_role_depth_terms.json")
    parser.add_argument("--out-md", type=Path, default=ROOT / "docs" / "external_role_depth_terms.md")
    parser.add_argument("--max-rows-per-file", type=int, default=40000)
    parser.add_argument("--max-file-mb", type=float, default=220.0)
    args = parser.parse_args()

    result = mine(args.external_dir, args.max_rows_per_file, args.max_file_mb)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, result)
    print(json.dumps({
        "status": "ok",
        "roles": result["role_rows"],
        "files_scanned": len(result["files"]),
        "out_json": str(args.out_json),
        "out_md": str(args.out_md),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
