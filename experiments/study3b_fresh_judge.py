"""Study 3b: independent fresh-judge confirmation (golden vs hedge).

Judges the UNION of golden's and hedge's top-100 with a frontier model the hedge was NEVER selected
against, addressing the one leak train/test splitting cannot (the Copeland-tail family was chosen
with the existing arbiter visible). Dev-only / read-only; submission.csv untouched. Output label
file is gitignored (never committed).

Run:  OPENAI_API_KEY=... OPENAI_BASE_URL=https://api.aicredits.in/v1 \
      python experiments/study3b_fresh_judge.py --model openai/gpt-5 [--limit N]
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
from llm_judge_labels import RUBRIC, compact_candidate  # noqa: E402

JD = Path("job_description.txt")


def judge_call(model, jd, cand, max_tokens):
    """OpenAI-compatible call with configurable max_tokens (reasoning models need headroom).
    base_url + key come from OPENAI_BASE_URL / OPENAI_API_KEY in the environment."""
    import json as _json
    from openai import OpenAI
    client = OpenAI()
    prompt = f"{RUBRIC}\n\n=== JOB DESCRIPTION ===\n{jd[:12000]}\n\n=== CANDIDATE ===\n{_json.dumps(cand, ensure_ascii=False)}"
    resp = client.chat.completions.create(model=model, max_tokens=max_tokens,
                                          messages=[{"role": "user", "content": prompt}])
    text = resp.choices[0].message.content or ""
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e < 0:
        raise ValueError(f"no JSON in response (len={len(text)})")
    return _json.loads(text[s:e + 1])


def submission_ids(text):
    return [r["candidate_id"] for r in csv.DictReader(text.splitlines())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="openai/gpt-5")
    ap.add_argument("--limit", type=int, default=0, help="probe: judge only N (0=all)")
    ap.add_argument("--out", default="experiments/fresh_judge_study3b.jsonl")
    ap.add_argument("--max-tokens", type=int, default=120,
                    help="raise for reasoning models that spend tokens on hidden thinking")
    args = ap.parse_args()
    OUT = Path(args.out)

    hedge = submission_ids(Path("submission.csv").read_text(encoding="utf-8"))
    golden = submission_ids(subprocess.run(
        ["git", "show", "fallback/golden-af8f2b32:submission.csv"],
        capture_output=True, text=True).stdout)
    union = list(dict.fromkeys(golden + hedge))  # stable, deduped
    print(f"golden={len(golden)} hedge={len(hedge)} union={len(union)} (overlap {len(set(golden)&set(hedge))})")

    done = {}
    if OUT.exists():
        for l in OUT.open(encoding="utf-8"):
            if l.strip():
                r = json.loads(l); done[r["candidate_id"]] = r
    todo = [c for c in union if c not in done]
    if args.limit:
        todo = todo[:args.limit]
    print(f"cached {len(done)}; judging {len(todo)} with {args.model} ...")

    jd = JD.read_text(encoding="utf-8")
    need = set(todo)
    recs = {}
    with open("candidates.jsonl", "rb") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            if c.get("candidate_id") in need:
                recs[c["candidate_id"]] = c
                if len(recs) == len(need):
                    break

    n_ok = 0
    with OUT.open("a", encoding="utf-8") as fh:
        for cid in todo:
            c = recs.get(cid)
            if c is None:
                print(f"  {cid}: no record"); continue
            try:
                v = judge_call(args.model, jd, compact_candidate(c), args.max_tokens)
                tier = int(v.get("tier", 0))
            except Exception as e:
                print(f"  {cid}: ERROR {e}"); continue
            fh.write(json.dumps({"candidate_id": cid, "tier": tier, "relevance": float(tier),
                                 "source": f"fresh:{args.model}", "why": v.get("why", "")}) + "\n")
            fh.flush(); n_ok += 1
    print(f"judged ok: {n_ok}  total cached now: {len(done)+n_ok}/{len(union)}  -> {OUT}")


if __name__ == "__main__":
    main()
