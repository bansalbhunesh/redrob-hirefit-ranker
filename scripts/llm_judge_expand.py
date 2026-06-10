#!/usr/bin/env python3
"""Calibration-expansion judging (dev-only): label a curated id set with gpt-4o-mini.

Training/validation side of the pre-registered challenger gate ONLY — these labels
are never added to the gate's scoring sources (judge #1/#2 + independent labels).

Selection (seeded, deterministic):
  - all gold-strata ids (21+8) lacking a judge-1 label
  - the full 150-profile 'machine learning engineer' stratum
  - seeded samples: 200 ds/ml, 150 software/data, 150 software-engineer, 50 filler
Usage:
    set OPENAI_API_KEY=...; python scripts/llm_judge_expand.py
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_judge_labels import RUBRIC, compact_candidate  # noqa: E402

_CLIENT = None


def judge_with_timeout(model: str, jd: str, cand: dict, base_url: str | None) -> dict:
    """Same prompt as llm_judge_labels.judge, with a hard 60s request timeout."""
    global _CLIENT
    from openai import OpenAI

    if _CLIENT is None:
        _CLIENT = OpenAI(base_url=base_url, timeout=60.0, max_retries=2)
    prompt = (f"{RUBRIC}\n\n=== JOB DESCRIPTION ===\n{jd[:12000]}\n\n"
              f"=== CANDIDATE ===\n{json.dumps(cand, ensure_ascii=False)}")
    resp = _CLIENT.chat.completions.create(
        model=model, max_tokens=120, messages=[{"role": "user", "content": prompt}])
    text = resp.choices[0].message.content
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])

STRATA_QUOTA = [
    ("senior ai engineer with # years", 999),
    ("senior engineer who has spent the", 999),
    ("machine learning engineer with # years", 999),
    ("data scientist / ml engineer with", 200),
    ("software / data professional with #", 150),
    ("software engineer with # years of", 150),
    ("professional with #+ years of experience#", 50),
]


def select_ids() -> list[str]:
    by_stratum: dict[str, list[str]] = {}
    for line in (ROOT / "artifacts" / "forensics_features.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        by_stratum.setdefault(r["summary_template"], []).append(r["candidate_id"])

    judged = {json.loads(l)["candidate_id"]
              for l in (ROOT / "docs" / "llm_judge_eval_labels.jsonl").open(encoding="utf-8")}

    rng = random.Random(42)
    chosen: list[str] = []
    for stratum, quota in STRATA_QUOTA:
        pool = sorted(by_stratum.get(stratum, []))
        rng.shuffle(pool)
        picked = [c for c in pool if c not in judged][:quota]
        chosen.extend(picked)
        print(f"  {stratum[:45]:47s} +{len(picked)}")
    return chosen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="openai/gpt-4o-mini")
    ap.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"))
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts" / "llm_labels_expand.jsonl")
    args = ap.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY not set.")

    target = set(select_ids())
    done: set[str] = set()
    if args.out.exists():
        done = {json.loads(l)["candidate_id"] for l in args.out.open(encoding="utf-8") if l.strip()}
    todo = target - done
    print(f"selected {len(target)}; cached {len(done)}; judging {len(todo)}")

    jd = (ROOT / "job_description.txt").read_text(encoding="utf-8")
    args.out.parent.mkdir(exist_ok=True)
    n_ok = n_err = 0
    with args.out.open("a", encoding="utf-8") as fh:
        for line in (ROOT / "candidates.jsonl").open(encoding="utf-8"):
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c["candidate_id"]
            if cid not in todo:
                continue
            try:
                verdict = judge_with_timeout(args.model, jd, compact_candidate(c), args.base_url)
                tier = int(verdict.get("tier", 0))
            except Exception as exc:  # noqa: BLE001
                n_err += 1
                print(f"  {cid}: error {type(exc).__name__}: {exc}", file=sys.stderr)
                time.sleep(1.0)
                continue
            fh.write(json.dumps({"candidate_id": cid, "tier": tier,
                                 "relevance": float(tier), "source": f"llm-expand:{args.model}",
                                 "why": verdict.get("why", "")}) + "\n")
            fh.flush()
            n_ok += 1
            if n_ok % 50 == 0:
                print(f"  {n_ok}/{len(todo)}")
    print(f"done: {n_ok} judged, {n_err} errors -> {args.out}")


if __name__ == "__main__":
    main()
