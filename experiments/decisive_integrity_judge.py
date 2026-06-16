"""Decisive, blinded, integrity-aware judge on the 56 candidates that differ between rrf-lock30 and
the hedge. The judge NEVER sees our scores or which ranking a candidate belongs to. Two separate
tasks per candidate:
  1. quality tier 0-5 (fit), independent of our scores.
  2. integrity_class for any tenure-date inconsistency:
       contradiction  = a real factual impossibility (tenure in a tech longer than it existed),
       ambiguity      = plausible rounding/overlap/resume imprecision, harmless,
       unsupported    = the detector is wrong; no real inconsistency,
       clean          = no flag.
Output: experiments/fresh_judge_decisive.jsonl  (gitignored). Reuses the aicredits gateway.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, "src"); sys.path.insert(0, "experiments"); sys.path.insert(0, "scripts")
from llm_judge_labels import compact_candidate
import anachronism

DIFF = Path("experiments/diff_rrf_vs_hedge.json")
OUT = Path("experiments/fresh_judge_decisive.jsonl")
JD = Path("job_description.txt")
MODEL = "openai/gpt-4.1"

RUBRIC = """You screen candidates for the attached Senior AI Engineer JD. Do TWO independent things.

(A) QUALITY: integer tier 0-5 for fit (5=exceptional: shipped production retrieval/ranking/recsys
search at a product company, 5-9 yrs, available; 4=strong, minor gap; 3=relevant w/ a notable gap;
2=adjacent/weak; 1=keyword overlap only/wrong role; 0=irrelevant or impossible profile). Read career
history, not just the skills list. Judge fit ONLY; ignore any ranking or score (none is given).

(B) INTEGRITY: if a tenure-date inconsistency is described below, classify it as exactly one of:
  "contradiction" - a real factual impossibility (e.g. claims more years in a technology than it has existed),
  "ambiguity"     - plausible rounding/role-overlap/resume imprecision; not disqualifying,
  "unsupported"   - the flag is wrong; the profile shows no real inconsistency.
If no inconsistency is described, use "clean".

Respond ONLY a JSON object: {"tier": <int 0-5>, "integrity": "<contradiction|ambiguity|unsupported|clean>", "why": "<=18 words"}."""


def judge(model, jd, cand, flag_detail):
    from openai import OpenAI
    client = OpenAI()
    block = f"\n\n=== FLAGGED TENURE-DATE INCONSISTENCY ===\n{flag_detail}" if flag_detail else \
            "\n\n(no tenure-date inconsistency detected for this profile)"
    prompt = f"{RUBRIC}\n\n=== JOB DESCRIPTION ===\n{jd[:11000]}\n\n=== CANDIDATE ===\n{json.dumps(cand, ensure_ascii=False)}{block}"
    r = client.chat.completions.create(model=model, max_tokens=140,
                                       messages=[{"role": "user", "content": prompt}])
    t = r.choices[0].message.content or ""
    s, e = t.find("{"), t.rfind("}")
    return json.loads(t[s:e + 1])


def flag_text(cand):
    v = anachronism.violations(cand)
    if not v:
        return None
    parts = []
    for x in v[:3]:
        if x["type"] == "skill_duration":
            parts.append(f"claims ~{x.get('claimed_years','?')}y in {x['tech']} but it is ~{x.get('max_years','?')}y old")
        else:
            parts.append(f"job ending {x.get('job_end_year','?')} names {x['tech']} (first available {x.get('tech_first_year','?')})")
    return "; ".join(parts)


def main():
    d = json.loads(DIFF.read_text())
    union = d["union_to_judge"]
    jd = JD.read_text(encoding="utf-8")
    need = set(union)
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
    done = {}
    if OUT.exists():
        for l in OUT.open(encoding="utf-8"):
            if l.strip():
                r = json.loads(l); done[r["candidate_id"]] = r
    todo = [c for c in union if c not in done]
    print(f"union {len(union)}; cached {len(done)}; judging {len(todo)} with {MODEL}")
    ok = 0
    with OUT.open("a", encoding="utf-8") as fh:
        for cid in todo:
            c = recs.get(cid)
            if c is None:
                print("missing", cid); continue
            try:
                v = judge(MODEL, jd, compact_candidate(c), flag_text(c))
            except Exception as e:
                print("err", cid, str(e)[:60]); continue
            fh.write(json.dumps({"candidate_id": cid, "tier": int(v.get("tier", 0)),
                                 "integrity": v.get("integrity", "clean"), "why": v.get("why", "")}) + "\n")
            fh.flush(); ok += 1
    print(f"judged ok {ok}; total {len(done)+ok}/{len(union)} -> {OUT}")


if __name__ == "__main__":
    main()
