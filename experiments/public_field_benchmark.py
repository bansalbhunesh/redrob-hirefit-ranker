"""Census and benchmark the public Redrob/India Runs repository field.

The scanner uses GitHub's REST API and raw-file service without executing any
third-party code.  It discovers repositories, inspects their trees, validates
public 100-row submission CSVs, and evaluates the strongest public artifact per
repository on the same local label worlds used for HireFit.

Outputs contain repository metadata and aggregate metrics only; competitor
candidate IDs and CSV contents are never persisted.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import io
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from redrob_ranker.eval_harness import LabelSet, load_labels, load_submission  # noqa: E402
from scripts.top100_ordering_audit import FastScorer  # noqa: E402


SEARCH_QUERIES = (
    "redrob in:name created:>=2026-04-01",
    '"India Runs" in:name,description created:>=2026-04-01',
)


@dataclass(frozen=True, slots=True)
class ArtifactMetrics:
    path: str
    h2: float
    mean7: float
    internal: dict[str, float]
    reviewer: float
    reviewer_coverage: float
    blind: float
    blind_coverage: float


def _token() -> str:
    return subprocess.check_output(["gh", "auth", "token"], text=True).strip()


class GitHubClient:
    def __init__(self, token: str) -> None:
        self.api_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-redrob-field-benchmark",
        }
        self.raw_headers = {"User-Agent": "codex-redrob-field-benchmark"}

    def json(self, url: str, retries: int = 4) -> tuple[Any | None, str | None]:
        for attempt in range(retries):
            try:
                with urlopen(Request(url, headers=self.api_headers), timeout=30) as response:
                    return json.loads(response.read().decode("utf-8")), None
            except HTTPError as exc:
                if exc.code in {403, 429, 502, 503} and attempt + 1 < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return None, f"HTTP {exc.code}"
            except Exception as exc:  # network errors are recorded, not fatal
                if attempt + 1 < retries:
                    time.sleep(attempt + 1)
                    continue
                return None, type(exc).__name__
        return None, "unreachable"

    def text(self, url: str, max_bytes: int = 2_500_000) -> str | None:
        try:
            with urlopen(Request(url, headers=self.raw_headers), timeout=25) as response:
                return response.read(max_bytes).decode("utf-8-sig", errors="replace")
        except Exception:
            return None


def _search(client: GitHubClient, query: str) -> list[dict[str, Any]]:
    url = "https://api.github.com/search/repositories?q=" + quote(query)
    first, error = client.json(url + "&per_page=100&page=1")
    if error or not isinstance(first, dict):
        raise RuntimeError(f"GitHub search failed for {query!r}: {error}")
    rows = list(first.get("items", []))
    pages = min(10, (min(int(first.get("total_count", 0)), 1000) + 99) // 100)
    for page in range(2, pages + 1):
        payload, page_error = client.json(url + f"&per_page=100&page={page}")
        if not page_error and isinstance(payload, dict):
            rows.extend(payload.get("items", []))
    print(f"search {query!r}: total={first.get('total_count')} retrieved={len(rows)}", flush=True)
    return rows


def parse_submission(text: str | None) -> list[str] | None:
    if not text:
        return None
    try:
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception:
        return None
    if len(rows) != 100 or not rows:
        return None
    columns = {str(key).strip().lower(): key for key in rows[0] if key}
    if "candidate_id" not in columns or "rank" not in columns:
        return None
    cid_key, rank_key = columns["candidate_id"], columns["rank"]
    try:
        rows.sort(key=lambda row: int(float(row[rank_key])))
        ranks = [int(float(row[rank_key])) for row in rows]
    except (KeyError, TypeError, ValueError):
        return None
    ids = [str(row[cid_key]).strip().strip('"') for row in rows]
    if ranks != list(range(1, 101)) or len(set(ids)) != 100:
        return None
    if sum(bool(re.match(r"^CAND[_-]?\d+", cid, re.I)) for cid in ids) < 90:
        return None
    return ids


def _csv_preference(path: str) -> int:
    lower = path.lower()
    base = lower.rsplit("/", 1)[-1]
    score = 0
    if "submission" in lower:
        score += 8
    if re.search(r"(ranked|ranking|final|official)", lower):
        score += 5
    if re.match(r"^[0-9a-f]{16,}\.csv$", base):
        score += 7
    if lower.startswith(("output/", "outputs/")):
        score += 3
    if any(
        token in lower
        for token in ("sample", "template", "reference", "metric", "report", "validation", "train")
    ):
        score -= 12
    return score


def tree_signals(paths: list[str]) -> tuple[int, dict[str, bool]]:
    lower = [path.lower() for path in paths]
    code = [path for path in lower if re.search(r"\.(py|js|jsx|ts|tsx|go|java|rs|ipynb)$", path)]
    non_notebook = [path for path in code if not path.endswith(".ipynb")]
    signals = {
        "readme": any(re.search(r"(^|/)readme(\.|$)", path) for path in lower),
        "src": any(path.startswith(("src/", "app/", "backend/", "api/", "packages/")) for path in lower),
        "tests": any(re.search(r"(^|/)(tests?/|test_|.*_test\.)", path) for path in lower),
        "docker": any(
            path.endswith("dockerfile") or "docker-compose" in path or "compose.yaml" in path
            for path in lower
        ),
        "ci": any(path.startswith(".github/workflows/") for path in lower),
        "deps": any(
            path.endswith(
                (
                    "requirements.txt",
                    "pyproject.toml",
                    "poetry.lock",
                    "uv.lock",
                    "package-lock.json",
                    "pnpm-lock.yaml",
                    "yarn.lock",
                )
            )
            for path in lower
        ),
        "eval": any(re.search(r"(eval|validation|benchmark|metric|ndcg|audit)", path) for path in lower),
        "submission": any(
            path.endswith(".csv") and re.search(r"(submission|ranked|ranking|output)", path)
            for path in lower
        ),
        "docs": any(
            path.startswith("docs/") and path.endswith((".md", ".pdf", ".pptx")) for path in lower
        ),
        "deploy": any(
            path.endswith(("render.yaml", "vercel.json", "procfile", "space.yaml"))
            or "streamlit" in path
            or "gradio" in path
            for path in lower
        ),
        "model": any(
            re.search(r"(model|rerank|embedding|lightgbm|xgboost|lambdamart|faiss)", path)
            for path in lower
        ),
        "artifact": any(path.endswith((".pkl", ".joblib", ".onnx", ".bin", ".pt", ".pth")) for path in lower),
        "notebook_only": bool(code) and not non_notebook,
    }
    weights = {
        "readme": 1,
        "src": 2,
        "tests": 3,
        "docker": 2,
        "ci": 2,
        "deps": 1,
        "eval": 2,
        "submission": 2,
        "docs": 1,
        "deploy": 1,
        "model": 1,
        "artifact": 1,
    }
    score = sum(weights[name] for name, present in signals.items() if present and name in weights)
    if len(non_notebook) < 3:
        score -= 2
    if signals["notebook_only"]:
        score -= 2
    return score, signals


def _evaluate_artifact(
    path: str,
    ids: list[str],
    names: list[str],
    scorers: list[FastScorer],
) -> ArtifactMetrics:
    values = {name: scorer.composite(ids) for name, scorer in zip(names[:7], scorers[:7], strict=True)}
    reviewer = scorers[7]
    blind = scorers[8]
    reviewer_scored = [cid for cid in ids if cid in reviewer.tiers]
    blind_scored = [cid for cid in ids if cid in blind.tiers]
    return ArtifactMetrics(
        path=path,
        h2=values["h2"],
        mean7=sum(values.values()) / len(values),
        internal=values,
        reviewer=reviewer.composite(ids),
        reviewer_coverage=len(reviewer_scored) / len(ids),
        blind=blind.composite(ids),
        blind_coverage=len(blind_scored) / len(ids),
    )


def scan_repository(
    client: GitHubClient,
    repository: dict[str, Any],
    names: list[str],
    scorers: list[FastScorer],
) -> dict[str, Any]:
    full_name = repository["full_name"]
    branch = repository.get("default_branch") or "main"
    tree, error = client.json(
        f"https://api.github.com/repos/{full_name}/git/trees/{quote(branch, safe='')}?recursive=1"
    )
    if error or not isinstance(tree, dict):
        return {"repo": full_name, "error": error}
    blobs = [item for item in tree.get("tree", []) if item.get("type") == "blob"]
    paths = [str(item.get("path", "")) for item in blobs]
    engineering_score, signals = tree_signals(paths)
    csv_items = [
        item
        for item in blobs
        if str(item.get("path", "")).lower().endswith(".csv")
        and int(item.get("size") or 0) <= 2_000_000
    ]
    csv_items.sort(
        key=lambda item: (_csv_preference(str(item["path"])), -int(item.get("size") or 0)),
        reverse=True,
    )
    artifacts: list[ArtifactMetrics] = []
    for item in csv_items[:12]:
        path = str(item["path"])
        raw_url = (
            f"https://raw.githubusercontent.com/{full_name}/{quote(branch, safe='')}/"
            f"{quote(path, safe='/[]')}"
        )
        ids = parse_submission(client.text(raw_url))
        if ids:
            artifacts.append(_evaluate_artifact(path, ids, names, scorers))
    # Give each competitor its best public H2 artifact. This is intentionally
    # adversarial/generous and is called out in the report.
    best = max(artifacts, key=lambda item: item.h2, default=None)
    return {
        "repo": full_name,
        "html_url": repository.get("html_url"),
        "updated_at": repository.get("updated_at"),
        "created_at": repository.get("created_at"),
        "size_kb": repository.get("size", 0),
        "stars": repository.get("stargazers_count", 0),
        "engineering_score": engineering_score,
        "signals": signals,
        "valid_artifact_count": len(artifacts),
        "best": asdict(best) if best else None,
    }


def _human_labels(path: Path, column: str) -> LabelSet:
    mapping = {"strong_fit": 4.0, "maybe": 2.0, "not_fit": 0.0}
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    values = {
        row["candidate_id"]: mapping[(row.get(column) or "").strip().lower()]
        for row in rows
        if (row.get(column) or "").strip().lower() in mapping
    }
    return LabelSet(column, values, dict(values))


def _label_sets(labels_root: Path, reviewer_csv: Path) -> tuple[list[str], list[LabelSet]]:
    sources = [
        ("h2", labels_root / "artifacts/h2_availblind_labels.jsonl"),
        ("independent", labels_root / "artifacts/independent_labels_100k.jsonl"),
        ("judge1", labels_root / "docs/llm_judge_eval_labels.jsonl"),
        ("judge2", labels_root / "docs/llm_judge_eval_2_labels.jsonl"),
        ("judge3", labels_root / "docs/llm_judge_eval_3_labels.jsonl"),
        ("expand", labels_root / "artifacts/llm_labels_expand.jsonl"),
        ("silver20k", labels_root / "artifacts/silver_labels_20k.jsonl"),
    ]
    names = [name for name, _ in sources] + ["reviewer", "blind"]
    sets = [load_labels(path, name) for name, path in sources]
    sets.extend(
        [
            _human_labels(reviewer_csv, "reviewer_label"),
            _human_labels(reviewer_csv, "technical_recruiter_label"),
        ]
    )
    return names, sets


def _local_baseline(
    name: str,
    path: Path,
    names: list[str],
    scorers: list[FastScorer],
    engineering_score: int,
) -> dict[str, Any]:
    ids = load_submission(path)
    metrics = _evaluate_artifact(str(path), ids, names, scorers)
    return {
        "repo": name,
        "engineering_score": engineering_score,
        "best": asdict(metrics),
    }


def strong_repository_names(rows: list[dict[str, Any]], limit: int = 15) -> list[str]:
    """Return the union of leaders on each defensible evaluation axis."""

    with_output = [row for row in rows if row.get("best")]
    selected: set[str] = set()
    axes = (
        lambda row: row["best"]["h2"],
        lambda row: row["best"]["mean7"],
        lambda row: row["best"]["reviewer"] if row["best"]["reviewer_coverage"] >= 0.30 else -1.0,
        lambda row: row["best"]["blind"] if row["best"]["blind_coverage"] >= 0.15 else -1.0,
    )
    for key in axes:
        selected.update(row["repo"] for row in sorted(with_output, key=key, reverse=True)[:limit])
    selected.update(
        row["repo"] for row in sorted(rows, key=lambda row: row["engineering_score"], reverse=True)[:limit]
    )
    return sorted(selected, key=str.lower)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels-root", required=True, type=Path)
    parser.add_argument("--reviewer-csv", required=True, type=Path)
    parser.add_argument("--main-submission", required=True, type=Path)
    parser.add_argument("--challenger-submission", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--strong-per-axis", type=int, default=15)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    names, label_sets = _label_sets(args.labels_root, args.reviewer_csv)
    scorers = [FastScorer(label_set) for label_set in label_sets]
    client = GitHubClient(_token())

    repositories: dict[str, dict[str, Any]] = {}
    for query in SEARCH_QUERIES:
        for repository in _search(client, query):
            repositories[repository["full_name"].lower()] = repository
    eligible = [
        repository
        for repository in repositories.values()
        if not repository.get("private")
        and not repository.get("fork")
        and not repository.get("archived")
        and int(repository.get("size") or 0) > 0
    ]
    print(f"unique={len(repositories)} eligible_public={len(eligible)}", flush=True)

    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = [
            executor.submit(scan_repository, client, repository, names, scorers)
            for repository in eligible
        ]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            rows.append(future.result())
            if index % 100 == 0:
                valid = sum(bool(row.get("best")) for row in rows)
                errors = sum(bool(row.get("error")) for row in rows)
                print(f"scanned={index} valid={valid} errors={errors}", flush=True)

    successful = [row for row in rows if not row.get("error")]
    baselines = [
        _local_baseline("LOCAL/main", args.main_submission, names, scorers, engineering_score=17),
        _local_baseline(
            "LOCAL/top23-clean", args.challenger_submission, names, scorers, engineering_score=17
        ),
    ]
    strong = strong_repository_names(successful, limit=args.strong_per_axis)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "queries": SEARCH_QUERIES,
        "discovered_unique": len(repositories),
        "eligible_public": len(eligible),
        "scanned_successfully": len(successful),
        "valid_output_repositories": sum(bool(row.get("best")) for row in successful),
        "selection_note": "best H2 artifact per repo; generous/adversarial to competitors",
        "baselines": baselines,
        "strong_repository_names": strong,
        "rows": sorted(successful, key=lambda row: row["repo"].lower()),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"wrote {args.out}; valid={payload['valid_output_repositories']} strong={len(strong)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
