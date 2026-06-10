#!/usr/bin/env python3
"""Judge-#2 pass (dev-only): re-judge the exact candidate set behind
docs/llm_judge_eval_labels.jsonl with a second, independent model family.

Same rubric, same field subset, same ids as judge #1 — so inter-judge
agreement (correlation, kappa) is computed on an identical sample rather
than a re-stratified one. Resumable like the original tool.

Usage:
    set OPENAI_API_KEY=...   (gateway key; never committed)
    python scripts/llm_judge_second.py --model openai/gpt-4.1-mini \
        --base-url https://api.aicredits.in/v1 \
        --out artifacts/llm_labels_judge2.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_judge_labels import RUBRIC, compact_candidate, judge  # noqa: E402

JUDGE1 = ROOT / "docs" / "llm_judge_eval_labels.jsonl"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=Path, default=ROOT / "candidates.jsonl")
    ap.add_argument("--jd", type=Path, default=ROOT / "job_description.txt")
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts" / "llm_labels_judge2.jsonl")
    ap.add_argument("--model", default="openai/gpt-4.1-mini")
    ap.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"))
    args = ap.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY not set (dev-only tool; ranking path never calls an LLM).")

    target = {json.loads(l)["candidate_id"] for l in JUDGE1.open(encoding="utf-8") if l.strip()}
    done: set[str] = set()
    if args.out.exists():
        done = {json.loads(l)["candidate_id"] for l in args.out.open(encoding="utf-8") if l.strip()}
    todo = target - done
    print(f"judge-1 sample: {len(target)} ids; cached: {len(done)}; judging {len(todo)}")

    jd = args.jd.read_text(encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    n_ok = n_err = 0
    with args.out.open("a", encoding="utf-8") as fh:
        for line in args.candidates.open(encoding="utf-8"):
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c["candidate_id"]
            if cid not in todo:
                continue
            try:
                verdict = judge("openai", args.model, jd, compact_candidate(c), args.base_url)
                tier = int(verdict.get("tier", 0))
            except Exception as exc:  # noqa: BLE001 - dev tool, keep going
                n_err += 1
                print(f"  {cid}: error {exc}", file=sys.stderr)
                time.sleep(1.0)
                continue
            fh.write(json.dumps({"candidate_id": cid, "tier": tier,
                                 "relevance": float(tier), "source": f"llm2:{args.model}",
                                 "why": verdict.get("why", "")}) + "\n")
            fh.flush()
            n_ok += 1
            if n_ok % 25 == 0:
                print(f"  {n_ok}/{len(todo)} judged")
    print(f"done: {n_ok} judged, {n_err} errors -> {args.out}")


if __name__ == "__main__":
    main()
