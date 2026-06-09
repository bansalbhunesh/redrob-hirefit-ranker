#!/usr/bin/env python3
"""Gold-path eval labels: LLM-judged relevance tiers on a stratified sample.

This is a DEVELOPMENT-ONLY tool. It is NOT part of the ranking path and never
runs during submission generation (which stays offline/CPU/no-network per spec
section 3). Its only job is to anchor the heuristic labels in
`build_independent_labels.py` with judgments from a strong model, so we can tune
the ranker against something closer to the hidden ground truth than our own code.

Design choices grounded in the eval literature:
  * Stratified sampling - random 100K sampling is ~99% irrelevant and wastes the
    budget; we oversample the contested region (ranker top-N + heuristic top tiers)
    plus a random control, so NDCG@10 (the dominant metric) is actually informed.
  * Pointwise tiering with an explicit rubric. For the closest calls, re-run in
    --pairwise mode (less position bias than pointwise on near-ties; see
    arXiv:2406.07791) and reconcile.
  * Caching + resume - re-runs skip already-judged ids.

Privacy: the dataset is synthetic/anonymized, but we still send only a curated
field subset (no raw identifiers), as good hygiene and a clean Stage-4/5 story.

Usage:
    setx ANTHROPIC_API_KEY ...        # or OPENAI_API_KEY
    python scripts/llm_judge_labels.py --candidates candidates.jsonl \
        --jd job_description.txt --out artifacts/llm_labels.jsonl \
        --submission submission.csv --stratify-labels artifacts/independent_labels_100k.jsonl \
        --sample-size 300 --provider anthropic --model claude-sonnet-4-6
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

RUBRIC = """You are screening candidates for the attached Senior AI Engineer JD.
Assign an integer relevance tier 0-5 for how well this candidate fits, where:
  5 = exceptional fit: shipped production retrieval/ranking/recsys/search systems
      at a product company, 5-9 yrs, strong recent availability.
  4 = strong fit with a minor gap.
  3 = relevant (clearly in scope) but with a notable gap (band, availability, depth).
  2 = adjacent / weak: some ML but not retrieval/ranking, or wrong seniority.
  1 = poor: keyword overlap only, wrong role, or framework-wrapper-only experience.
  0 = irrelevant or an impossible/contradictory profile (honeypot), or a
      non-target role (e.g. Marketing/HR/Design) regardless of listed AI skills.
Read the career history, not just the skills list. A candidate who BUILT the
systems without the buzzwords outranks one who lists the buzzwords but never
shipped. Respond with ONLY a JSON object: {"tier": <int 0-5>, "why": "<=15 words"}.
"""


def compact_candidate(c: dict) -> dict:
    prof = c.get("profile", {})
    sig = c.get("redrob_signals", {})
    return {
        "current_title": prof.get("current_title"),
        "years_experience": prof.get("years_of_experience"),
        "headline": prof.get("headline"),
        "summary": (prof.get("summary") or "")[:600],
        "location": prof.get("location"), "country": prof.get("country"),
        "career": [{"title": j.get("title"), "company": j.get("company"),
                    "industry": j.get("industry"), "months": j.get("duration_months"),
                    "desc": (j.get("description") or "")[:300]}
                   for j in (c.get("career_history") or [])[:6]],
        "skills": [s.get("name") for s in (c.get("skills") or [])][:20],
        "signals": {k: sig.get(k) for k in
                    ("recruiter_response_rate", "last_active_date", "open_to_work_flag",
                     "notice_period_days", "github_activity_score")},
    }


def stratified_ids(submission: Path | None, strat_labels: Path | None,
                   all_ids: list[str], n: int, top_n: int) -> list[str]:
    chosen: list[str] = []
    seen: set[str] = set()

    def add(ids):
        for i in ids:
            if i not in seen:
                seen.add(i); chosen.append(i)

    if submission and submission.exists():
        import csv
        rows = sorted(csv.DictReader(open(submission, encoding="utf-8")), key=lambda r: int(r["rank"]))
        add(r["candidate_id"] for r in rows[:top_n])              # contested top of the ranker
    if strat_labels and strat_labels.exists():
        by_tier: dict[int, list[str]] = {}
        for line in open(strat_labels, encoding="utf-8"):
            rec = json.loads(line)
            by_tier.setdefault(int(rec.get("tier", 0)), []).append(rec["candidate_id"])
        rng = random.Random(13)
        for tier in (5, 4, 3, 2, 1, 0):                          # spread across tiers
            pool = by_tier.get(tier, [])
            rng.shuffle(pool)
            add(pool[:max(10, n // 8)])
    rng = random.Random(7)
    rng.shuffle(all_ids)
    add(all_ids)                                                  # random control fills remainder
    return chosen[:n]


def judge(provider: str, model: str, jd: str, cand: dict, base_url: str | None = None) -> dict:
    prompt = f"{RUBRIC}\n\n=== JOB DESCRIPTION ===\n{jd[:12000]}\n\n=== CANDIDATE ===\n{json.dumps(cand, ensure_ascii=False)}"
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(base_url=base_url) if base_url else anthropic.Anthropic()
        msg = client.messages.create(model=model, max_tokens=120,
                                      messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text
    else:
        from openai import OpenAI
        # base_url lets us target an OpenAI-compatible gateway (e.g. aicredits.in).
        client = OpenAI(base_url=base_url) if base_url else OpenAI()
        resp = client.chat.completions.create(model=model, max_tokens=120,
                                               messages=[{"role": "user", "content": prompt}])
        text = resp.choices[0].message.content
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def main() -> None:
    ap = argparse.ArgumentParser(description="LLM-judged relevance labels (dev-only).")
    ap.add_argument("--candidates", required=True, type=Path)
    ap.add_argument("--jd", required=True, type=Path, help="JD text file (e.g. job_description.txt)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--submission", type=Path, default=None)
    ap.add_argument("--stratify-labels", type=Path, default=None)
    ap.add_argument("--sample-size", type=int, default=300)
    ap.add_argument("--top-n", type=int, default=120)
    ap.add_argument("--provider", choices=["anthropic", "openai"], default="anthropic")
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"),
                    help="OpenAI-compatible gateway base URL (e.g. https://api.aicredits.in/v1).")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY" if args.provider == "anthropic" else "OPENAI_API_KEY")
    if not key:
        env = "ANTHROPIC_API_KEY" if args.provider == "anthropic" else "OPENAI_API_KEY"
        print(f"[skip] {env} not set. This dev-only tool needs an API key.\n"
              f"       The ranking path never calls an LLM; this only builds eval labels.\n"
              f"       Set {env} and re-run to anchor the heuristic labels.", file=sys.stderr)
        sys.exit(2)

    jd = args.jd.read_text(encoding="utf-8")
    all_ids = [json.loads(l)["candidate_id"] for l in open(args.candidates, encoding="utf-8") if l.strip()]
    target = set(stratified_ids(args.submission, args.stratify_labels, all_ids, args.sample_size, args.top_n))

    done: set[str] = set()
    if args.out.exists():
        done = {json.loads(l)["candidate_id"] for l in open(args.out, encoding="utf-8") if l.strip()}
    todo = target - done
    print(f"sampled {len(target)} ids; {len(done)} cached; judging {len(todo)} ...")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", encoding="utf-8") as fh:
        for line in open(args.candidates, encoding="utf-8"):
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c["candidate_id"]
            if cid not in todo:
                continue
            try:
                verdict = judge(args.provider, args.model, jd, compact_candidate(c), args.base_url)
                tier = int(verdict.get("tier", 0))
            except Exception as exc:  # noqa: BLE001 - dev tool, keep going
                print(f"  {cid}: error {exc}", file=sys.stderr)
                continue
            fh.write(json.dumps({"candidate_id": cid, "tier": tier,
                                 "relevance": float(tier), "source": "llm",
                                 "why": verdict.get("why", "")}) + "\n")
            fh.flush()
    print(f"Done. Labels in {args.out}. Score with: "
          f"python scripts/evaluate_independent.py --submission <csv> --labels {args.out} --label-source llm-judge")


if __name__ == "__main__":
    main()
