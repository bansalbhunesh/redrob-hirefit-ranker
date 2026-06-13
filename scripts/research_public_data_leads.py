#!/usr/bin/env python3
"""Collect public research leads for the Redrob ranking gap lab.

This script intentionally uses only public, unauthenticated sources. It does
not scrape logged-in X/Twitter, LinkedIn, or gated pages, and it does not touch
the deterministic ranking path.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as DET


ROOT = Path(__file__).resolve().parents[1]

HEADERS = {
    "User-Agent": (
        "india-runs-public-data-leads/1.0 "
        "(public research collector; no login or protected scraping)"
    )
}

OFFICIAL_PAGES = [
    "https://hack2skill.com/event/india_runs",
    "https://redrob.io/",
    "https://redrob.io/resume-ranker",
    "https://redrob.io/people-search",
    "https://redrob.io/job-search",
    "https://redrob.io/company-search",
]

HF_DATASETS = [
    "cnamuangtoun/resume-job-description-fit",
    "0xnbk/resume-ats-score-v1-en",
    "facehuggerapoorv/resume-jd-match",
    "layan009/RESUMES-JOBS-FIT-LABELS",
    "netsol/resume-score-details",
    "emrekuruu/job-search-distill",
    "AzharAli05/Resume-Screening-Dataset",
    "batuhanmtl/job-skill-set",
    "jacob-hugging-face/job-descriptions",
]

REDDIT_THREADS = [
    {
        "name": "AI resume screening should be illegal",
        "url": (
            "https://old.reddit.com/r/recruitinghell/comments/1gvcpz4/"
            "ai_resume_screening_should_be_illegal/"
        ),
    },
    {
        "name": "Employers buried in AI-generated resumes",
        "url": (
            "https://old.reddit.com/r/recruitinghell/comments/1lk9uty/"
            "employers_are_buried_in_aigenerated_r%C3%A9sum%C3%A9s/"
        ),
    },
    {
        "name": "Best way through AI job filters",
        "url": (
            "https://old.reddit.com/r/cscareerquestions/comments/1kt12kw/"
            "whats_the_best_way_to_get_through_ai_job_filters/"
        ),
    },
    {
        "name": "HireVue AI screening discussion",
        "url": (
            "https://old.reddit.com/r/MachineLearning/comments/cmihda/"
            "d_company_hirevue_provides_ai_for_earlystage/"
        ),
    },
]

GITHUB_QUERIES = [
    "candidate ranking AI resume job fit scoring",
    "resume job matching learning to rank nDCG",
    "recruitment ai resume ranking cross encoder",
    "job candidate matching bm25 embeddings ranker",
    "ATS resume scoring job description match",
]

ARXIV_QUERIES = [
    'all:"job candidate matching" OR all:"person job fit"',
    'all:"resume job matching" AND all:"learning to rank"',
    'all:"job recommendation" AND all:"resume" AND all:"ranking"',
    'all:"ConFit" AND all:"job" AND all:"resume"',
]

SOCIAL_SEARCH_QUERIES = [
    "site:x.com Redrob AI India Runs Track 1 candidate ranking",
    "site:x.com redrob.io resume ranker candidate ranking",
    "site:linkedin.com/posts Redrob AI India Runs Track 1 candidate ranking",
    "site:twitter.com Redrob AI India Runs Track 1 candidate ranking",
]

OFFICIAL_KEYWORDS = [
    "Contextual Relevance",
    "Signal Integration",
    "ranked shortlist",
    "ranked output file",
    "June 2026",
    "July 2026",
    "700M",
    "15M",
    "30+",
    "27 more Indian languages",
    "match score",
    "skill match",
    "experience depth",
    "role relevance",
    "Export to CSV",
    "CRM",
    "multilingual",
]

REDDIT_FAILURE_TERMS = {
    "ats": r"\bATS\b",
    "ai": r"\bAI\b|A\.I\.",
    "keyword": r"\bkeyword",
    "filter": r"\bfilter",
    "referral": r"\breferral",
    "tailor": r"\btailor|\boptimi[sz]e",
    "spam": r"\bspam",
    "bias": r"\bbias|illegal|discrimin",
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            text = data.strip()
            if text:
                self.parts.append(text)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def fetch_text(url: str, *, timeout: int = 30) -> tuple[int | None, str, str | None]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None, "", f"unsupported URL scheme: {parsed.scheme or '<empty>'}"
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            return response.status, response.read().decode("utf-8", errors="replace"), None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body, str(exc)
    except (TimeoutError, urllib.error.URLError) as exc:
        return None, "", str(exc)


def html_text(raw_html: str) -> str:
    parser = TextExtractor()
    parser.feed(raw_html)
    return html.unescape(parser.text())


def snippet(text: str, needle: str, *, radius: int = 160) -> str | None:
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return None
    start = max(0, idx - radius)
    end = min(len(text), idx + len(needle) + radius)
    return text[start:end]


def collect_official_pages() -> list[dict[str, Any]]:
    pages = []
    for url in OFFICIAL_PAGES:
        status, raw, error = fetch_text(url)
        text = html_text(raw) if raw else ""
        pages.append(
            {
                "url": url,
                "status": status,
                "error": error,
                "text_length": len(text),
                "text_start": text[:260],
                "snippets": {
                    key: hit
                    for key in OFFICIAL_KEYWORDS
                    if (hit := snippet(text, key)) is not None
                },
            }
        )
    return pages


def collect_hf_datasets() -> list[dict[str, Any]]:
    out = []
    for dataset in HF_DATASETS:
        api_url = f"https://huggingface.co/api/datasets/{dataset}"
        status, raw, error = fetch_text(api_url)
        record: dict[str, Any] = {
            "dataset": dataset,
            "url": f"https://huggingface.co/datasets/{dataset}",
            "api_status": status,
            "error": error,
        }
        if status == 200 and raw:
            meta = json.loads(raw)
            card = meta.get("cardData") or {}
            siblings = meta.get("siblings") or []
            record.update(
                {
                    "downloads": meta.get("downloads"),
                    "likes": meta.get("likes"),
                    "last_modified": meta.get("lastModified"),
                    "private": meta.get("private"),
                    "gated": meta.get("gated"),
                    "license": card.get("license"),
                    "tags": (meta.get("tags") or [])[:12],
                    "files": [item.get("rfilename") for item in siblings[:12]],
                }
            )
        for split in ("train", "test", "validation"):
            params = urllib.parse.urlencode(
                {"dataset": dataset, "config": "default", "split": split}
            )
            first_rows_url = f"https://datasets-server.huggingface.co/first-rows?{params}"
            first_status, first_raw, first_error = fetch_text(first_rows_url, timeout=45)
            if first_status == 200 and first_raw:
                payload = json.loads(first_raw)
                rows = payload.get("rows") or []
                first_row = rows[0].get("row", {}) if rows else {}
                record["first_rows"] = {
                    "split": split,
                    "status": first_status,
                    "features": payload.get("features"),
                    "row_count_returned": len(rows),
                    "first_row_keys": list(first_row.keys()),
                    "first_row_preview": {
                        key: (value[:180] if isinstance(value, str) else value)
                        for key, value in list(first_row.items())[:5]
                    },
                }
                break
            if first_status not in {400, 404}:
                record.setdefault("first_rows_errors", []).append(
                    {"split": split, "status": first_status, "error": first_error}
                )
        out.append(record)
    return out


def collect_reddit_threads() -> list[dict[str, Any]]:
    out = []
    for thread in REDDIT_THREADS:
        status, raw, error = fetch_text(thread["url"])
        text = html_text(raw) if raw else ""
        title_match = re.search(r"<title>(.*?)</title>", raw or "", re.I | re.S)
        score_match = re.search(r'data-score="([^"]+)"', raw or "")
        comments = re.findall(r'class="[^"]*\bcomment\b[^"]*"', raw or "")
        term_counts = {
            name: len(re.findall(pattern, text, flags=re.I))
            for name, pattern in REDDIT_FAILURE_TERMS.items()
        }
        out.append(
            {
                "name": thread["name"],
                "url": thread["url"],
                "status": status,
                "error": error,
                "title": html.unescape(title_match.group(1)) if title_match else None,
                "post_score": score_match.group(1) if score_match else None,
                "comment_nodes": len(comments),
                "failure_term_counts": term_counts,
                "use": "qualitative failure modes only; not labels or training data",
            }
        )
    return out


def collect_github_repos() -> list[dict[str, Any]]:
    repos: dict[str, dict[str, Any]] = {}
    for query in GITHUB_QUERIES:
        params = urllib.parse.urlencode(
            {"q": query, "sort": "stars", "order": "desc", "per_page": "8"}
        )
        status, raw, error = fetch_text(
            f"https://api.github.com/search/repositories?{params}"
        )
        if status != 200 or not raw:
            repos[f"query_error:{query}"] = {
                "query": query,
                "status": status,
                "error": error,
            }
            continue
        for item in json.loads(raw).get("items", []):
            repos.setdefault(
                item["full_name"],
                {
                    "full_name": item["full_name"],
                    "url": item["html_url"],
                    "stars": item["stargazers_count"],
                    "language": item["language"],
                    "updated_at": item["updated_at"],
                    "description": item.get("description"),
                    "matched_queries": [],
                },
            )["matched_queries"].append(query)
    return sorted(
        (repo for key, repo in repos.items() if not key.startswith("query_error:")),
        key=lambda item: item["stars"],
        reverse=True,
    )[:20]


def collect_arxiv() -> list[dict[str, Any]]:
    papers: dict[str, dict[str, Any]] = {}
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for query in ARXIV_QUERIES:
        params = urllib.parse.urlencode(
            {
                "search_query": query,
                "start": "0",
                "max_results": "5",
                "sortBy": "lastUpdatedDate",
                "sortOrder": "descending",
            }
        )
        status, raw, _ = fetch_text(f"https://export.arxiv.org/api/query?{params}")
        if status != 200 or not raw:
            continue
        root = DET.fromstring(raw)
        for entry in root.findall("atom:entry", ns):
            title = re.sub(r"\s+", " ", entry.findtext("atom:title", "", ns)).strip()
            paper_id = entry.findtext("atom:id", "", ns)
            summary = re.sub(r"\s+", " ", entry.findtext("atom:summary", "", ns)).strip()
            papers.setdefault(
                paper_id,
                {
                    "title": title,
                    "url": paper_id,
                    "published": entry.findtext("atom:published", "", ns)[:10],
                    "updated": entry.findtext("atom:updated", "", ns)[:10],
                    "summary_preview": summary[:360],
                    "matched_queries": [],
                },
            )["matched_queries"].append(query)
    return sorted(papers.values(), key=lambda item: item["updated"], reverse=True)


def collect_social_search() -> list[dict[str, Any]]:
    results = []
    for query in SOCIAL_SEARCH_QUERIES:
        params = urllib.parse.urlencode({"q": query})
        status, raw, error = fetch_text(f"https://duckduckgo.com/html/?{params}")
        text = html_text(raw) if raw else ""
        # DuckDuckGo often returns 202 challenge/interstitial responses. Preserve that
        # state so the report does not overclaim social-source coverage.
        links = re.findall(r'class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', raw or "")
        parsed_links = [
            {"href": html.unescape(href), "title": re.sub(r"<[^>]+>", "", title)}
            for href, title in links[:5]
        ]
        results.append(
            {
                "query": query,
                "status": status,
                "error": error,
                "text_length": len(text),
                "result_count_returned": len(parsed_links),
                "top_results": parsed_links,
                "use": "lead discovery only; no protected/logged-in scraping",
            }
        )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "public_data_leads.json",
        help="JSON output path (default: artifacts/public_data_leads.json)",
    )
    parser.add_argument(
        "--skip-social-search",
        action="store_true",
        help="Skip DuckDuckGo social lead queries.",
    )
    args = parser.parse_args(argv)

    payload: dict[str, Any] = {
        "scope": "public unauthenticated research leads only",
        "official_pages": collect_official_pages(),
        "huggingface_datasets": collect_hf_datasets(),
        "reddit_threads": collect_reddit_threads(),
        "github_repositories": collect_github_repos(),
        "arxiv_papers": collect_arxiv(),
    }
    if not args.skip_social_search:
        payload["social_search"] = collect_social_search()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"HF datasets: {len(payload['huggingface_datasets'])}")
    print(f"Reddit threads: {len(payload['reddit_threads'])}")
    print(f"GitHub repos: {len(payload['github_repositories'])}")
    print(f"ArXiv papers: {len(payload['arxiv_papers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
