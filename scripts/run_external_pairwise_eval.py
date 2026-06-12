#!/usr/bin/env python3
"""Blind external pairwise fit evaluation on public resume/JD datasets.

This is deliberately separate from the Redrob dev-proxy labels. It scores
resume/JD pairs whose labels come from an external public dataset and does not
tune the ranker. Unsupported non-technical JDs are reported and skipped by
default; treating a sales/accounting JD as a failed AI-ranking eval would be
fake rigor.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.features import compute_features, final_score  # noqa: E402
from redrob_ranker.jd_compiler import compile_jd  # noqa: E402

CNAM_TEST_URL = (
    "https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit/"
    "resolve/main/test.csv"
)
CNAM_DATASET_URL = "https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit"
LABEL_TO_TIER = {"No Fit": 0.0, "Potential Fit": 3.0, "Good Fit": 5.0}

TITLE_HINTS = (
    "senior software engineer",
    "software engineer",
    "software developer",
    "full stack developer",
    "backend engineer",
    "java developer",
    "frontend engineer",
    "web developer",
    "business intelligence developer",
    "bi developer",
    "data analyst",
    "data engineer",
    "analytics engineer",
    "devops engineer",
    "site reliability engineer",
    "cloud engineer",
    "machine learning engineer",
    "ml engineer",
    "ai engineer",
)

COMMON_SKILLS = (
    "python", "java", "javascript", "typescript", "react", "node.js", "nodejs",
    "c#", ".net", "spring boot", "sql", "power bi", "tableau", "snowflake",
    "redshift", "etl", "aws", "azure", "gcp", "docker", "kubernetes",
    "terraform", "fastapi", "flask", "spark", "kafka", "pandas", "numpy",
    "machine learning", "data warehouse", "rest api", "microservices",
)

TOKEN_RE = re.compile(r"[a-z0-9+#.]{2,}")
YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\b", re.I)


@dataclass(frozen=True, slots=True)
class PairScore:
    pair_id: str
    label: str
    tier: float
    hirefit_score: float
    keyword_score: float
    jd_family: str


def download_if_missing(path: Path, url: str = CNAM_TEST_URL) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response, path.open("wb") as out:
        out.write(response.read())


def _tokens(text: str) -> set[str]:
    return {m.group(0) for m in TOKEN_RE.finditer(text.lower())}


def keyword_overlap(resume_text: str, jd_text: str) -> float:
    resume = _tokens(resume_text)
    jd = {t for t in _tokens(jd_text) if len(t) > 2}
    if not resume or not jd:
        return 0.0
    return len(resume & jd) / math.sqrt(len(resume) * len(jd))


def infer_years(*texts: str) -> float:
    years: list[float] = []
    for text in texts:
        for match in YEARS_RE.finditer(text or ""):
            try:
                value = float(match.group(1))
            except ValueError:
                continue
            if 0 <= value <= 40:
                years.append(value)
    if not years:
        return 5.0
    return max(1.0, min(max(years), 15.0))


def infer_title(resume_text: str, jd_text: str) -> str:
    blob = f" {resume_text.lower()} "
    for title in TITLE_HINTS:
        if f" {title} " in blob:
            return title.title()
    return "External Candidate"


def _skill_records(resume_text: str, compiled_jd) -> list[dict]:
    text_l = resume_text.lower()
    aliases: list[str] = list(COMMON_SKILLS)
    for _, group_aliases in compiled_jd.must_have_skills:
        aliases.extend(group_aliases)
    for _, group_aliases in compiled_jd.nice_to_have_skills:
        aliases.extend(group_aliases)

    seen: set[str] = set()
    records: list[dict] = []
    for alias in aliases:
        key = alias.lower()
        if key in seen or key not in text_l:
            continue
        seen.add(key)
        records.append({
            "name": alias,
            "proficiency": "advanced",
            "endorsements": 8,
            "duration_months": 36,
        })
        if len(records) >= 18:
            break
    return records


def external_candidate(pair_id: str, resume_text: str, jd_text: str, compiled_jd) -> dict:
    years = infer_years(resume_text, jd_text)
    title = infer_title(resume_text, jd_text)
    return {
        "candidate_id": pair_id,
        "profile": {
            "current_title": title,
            "headline": title,
            "summary": resume_text[:4000],
            "location": "India",
            "country": "India",
            "years_of_experience": years,
            "current_company": "External Dataset",
            "current_industry": "Software",
            "current_company_size": "501-1000",
        },
        "career_history": [{
            "company": "External Dataset",
            "title": title,
            "start_date": "2020-01-01",
            "end_date": None,
            "is_current": True,
            "duration_months": int(years * 12),
            "industry": "Software",
            "company_size": "501-1000",
            "description": resume_text[:12000],
        }],
        "education": [],
        "certifications": [],
        "languages": [],
        "skills": _skill_records(resume_text, compiled_jd),
        "redrob_signals": {
            "last_active_date": "2026-05-20",
            "open_to_work_flag": True,
            "recruiter_response_rate": 0.55,
            "avg_response_time_hours": 24,
            "interview_completion_rate": 0.80,
            "saved_by_recruiters_30d": 3,
            "notice_period_days": 30,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
            "willing_to_relocate": True,
            "github_activity_score": 20,
            "profile_completeness_score": 85,
        },
    }


def score_pair(pair_id: str, resume_text: str, jd_text: str, label: str) -> PairScore | None:
    try:
        compiled = compile_jd(jd_text, source=f"external:{pair_id}")
    except ValueError:
        return None
    candidate = external_candidate(pair_id, resume_text, jd_text, compiled)
    features = compute_features(candidate, config=compiled)
    lexical = keyword_overlap(resume_text, compiled.jd_query or jd_text)
    score = final_score(features, retrieval_score=lexical, config=compiled)
    family = next(
        (name for name, weight in compiled.target_title_weights if weight >= 0.94),
        "compiled_technical",
    )
    return PairScore(
        pair_id=pair_id,
        label=label,
        tier=LABEL_TO_TIER[label],
        hirefit_score=score,
        keyword_score=keyword_overlap(resume_text, jd_text),
        jd_family=family,
    )


def roc_auc(scores: list[float], labels: list[int]) -> float:
    positives = [s for s, y in zip(scores, labels) if y == 1]
    negatives = [s for s, y in zip(scores, labels) if y == 0]
    if not positives or not negatives:
        return 0.0
    wins = 0.0
    total = len(positives) * len(negatives)
    for ps in positives:
        for ns in negatives:
            if ps > ns:
                wins += 1.0
            elif ps == ns:
                wins += 0.5
    return wins / total


def _rankdata(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for pos in range(i, j):
            ranks[order[pos]] = avg_rank
        i = j
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    num = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    xden = math.sqrt(sum((x - xbar) ** 2 for x in xs))
    yden = math.sqrt(sum((y - ybar) ** 2 for y in ys))
    if xden <= 0 or yden <= 0:
        return 0.0
    return num / (xden * yden)


def spearman(xs: list[float], ys: list[float]) -> float:
    return pearson(_rankdata(xs), _rankdata(ys))


def summarize(scores: list[PairScore], total_rows: int, unsupported: int) -> dict:
    tiers = [s.tier for s in scores]
    hirefit = [s.hirefit_score for s in scores]
    keyword = [s.keyword_score for s in scores]
    positive_any = [1 if t >= 3.0 else 0 for t in tiers]
    positive_good = [1 if t >= 5.0 else 0 for t in tiers]

    by_label: dict[str, list[float]] = defaultdict(list)
    by_family = Counter()
    for score in scores:
        by_label[score.label].append(score.hirefit_score)
        by_family[score.jd_family] += 1

    ordered = sorted(scores, key=lambda s: s.hirefit_score, reverse=True)
    top_n = max(1, len(ordered) // 10)
    top_decile = ordered[:top_n]
    bottom_decile = ordered[-top_n:]
    goodish = {"Good Fit", "Potential Fit"}

    return {
        "source": CNAM_DATASET_URL,
        "split": "test.csv",
        "total_rows": total_rows,
        "scored_supported_rows": len(scores),
        "unsupported_rows": unsupported,
        "coverage": round(len(scores) / total_rows, 4) if total_rows else 0.0,
        "label_distribution": dict(Counter(s.label for s in scores)),
        "top_compiled_families": dict(by_family.most_common(12)),
        "hirefit_auc_good_or_potential": round(roc_auc(hirefit, positive_any), 4),
        "keyword_auc_good_or_potential": round(roc_auc(keyword, positive_any), 4),
        "hirefit_auc_good_only": round(roc_auc(hirefit, positive_good), 4),
        "keyword_auc_good_only": round(roc_auc(keyword, positive_good), 4),
        "hirefit_spearman_tier": round(spearman(hirefit, tiers), 4),
        "keyword_spearman_tier": round(spearman(keyword, tiers), 4),
        "mean_hirefit_score_by_label": {
            label: round(sum(values) / len(values), 4)
            for label, values in sorted(by_label.items())
        },
        "top_decile_good_or_potential_rate": round(
            sum(1 for s in top_decile if s.label in goodish) / len(top_decile), 4
        ),
        "bottom_decile_good_or_potential_rate": round(
            sum(1 for s in bottom_decile if s.label in goodish) / len(bottom_decile), 4
        ),
    }


def evaluate_cnam(path: Path, max_rows: int | None = None) -> tuple[dict, list[PairScore]]:
    scores: list[PairScore] = []
    total = 0
    unsupported = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            label = row.get("label", "")
            if label not in LABEL_TO_TIER:
                continue
            total += 1
            pair = score_pair(
                pair_id=f"EXT_CNAM_{idx:05d}",
                resume_text=row.get("resume_text", ""),
                jd_text=row.get("job_description_text", ""),
                label=label,
            )
            if pair is None:
                unsupported += 1
            else:
                scores.append(pair)
            if max_rows is not None and total >= max_rows:
                break
    return summarize(scores, total, unsupported), scores


def write_markdown(path: Path, summary: dict) -> None:
    lines = [
        "# External Blind Pairwise Fit Evaluation",
        "",
        "This is external public-label evidence, not official Redrob hidden-label evidence.",
        "",
        f"- Source: {summary['source']}",
        f"- Split: `{summary['split']}`",
        f"- Rows read: {summary['total_rows']:,}",
        f"- Supported technical rows scored: {summary['scored_supported_rows']:,}",
        f"- Unsupported rows skipped: {summary['unsupported_rows']:,}",
        f"- Coverage: {summary['coverage']:.1%}",
        "",
        "## Metrics",
        "",
        "| metric | HireFit | keyword-overlap baseline |",
        "|---|---:|---:|",
        f"| AUC, Good/Potential vs No Fit | {summary['hirefit_auc_good_or_potential']:.4f} | {summary['keyword_auc_good_or_potential']:.4f} |",
        f"| AUC, Good Fit vs rest | {summary['hirefit_auc_good_only']:.4f} | {summary['keyword_auc_good_only']:.4f} |",
        f"| Spearman vs 0/3/5 tier | {summary['hirefit_spearman_tier']:.4f} | {summary['keyword_spearman_tier']:.4f} |",
        "",
        "## Label Means",
        "",
        "| external label | mean HireFit score |",
        "|---|---:|",
    ]
    for label, value in summary["mean_hirefit_score_by_label"].items():
        lines.append(f"| {label} | {value:.4f} |")
    lines.extend([
        "",
        "## Decile Lift",
        "",
        f"- Top decile Good/Potential rate: {summary['top_decile_good_or_potential_rate']:.1%}",
        f"- Bottom decile Good/Potential rate: {summary['bottom_decile_good_or_potential_rate']:.1%}",
        "",
        "## Limits",
        "",
        "- The public dataset labels are external, but they are not the hackathon hidden labels.",
        "- This is pairwise fit scoring across many JDs, not a same-JD top-100 ranking leaderboard.",
        "- Unsupported non-technical JDs are skipped by design because this ranker targets technical hiring.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run external public pairwise fit evaluation.")
    parser.add_argument("--cnam-test", type=Path, default=ROOT / "artifacts" / "external_cnam_test.csv")
    parser.add_argument("--download", action="store_true", help="Download cnamuangtoun test.csv if missing.")
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--out-json", type=Path, default=ROOT / "artifacts" / "external_pairwise_eval.json")
    parser.add_argument("--out-md", type=Path, default=ROOT / "docs" / "external_blind_pairwise_eval.md")
    args = parser.parse_args()

    if args.download:
        download_if_missing(args.cnam_test)
    if not args.cnam_test.exists():
        raise SystemExit(f"Missing dataset: {args.cnam_test}. Re-run with --download.")

    summary, _ = evaluate_cnam(args.cnam_test, max_rows=args.max_rows)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
