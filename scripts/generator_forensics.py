#!/usr/bin/env python3
"""Generator forensics (dev-only): recover the synthetic generator's latent structure.

The planted honeypots prove the 100K pool was produced by a generator with explicit
per-profile quality logic (summary-vs-field YoE contradictions, sitcom company pools,
tiered education fields). This tool extracts those latent variables per candidate so a
challenger model (docs/ltr_challenger_gate.md) can use them as features, and prints a
population study of the recovered structure.

Outputs artifacts/forensics_features.jsonl (one record per candidate) and a summary.
NOT part of the ranking path.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

try:
    import orjson as _json

    def loads(b):
        return _json.loads(b)
except ImportError:
    def loads(b):
        return json.loads(b)

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DATE = date(2026, 6, 8)

STATED_YOE = re.compile(r"with\s+([\d.]+)\s+years?\s+of\s+experience", re.I)

# Company pools the generator draws from (curated from the released data).
SITCOM = {"hooli", "globex inc", "globex", "initech", "acme corp", "acme", "pied piper",
          "dunder mifflin", "stark industries", "wayne enterprises", "umbrella corp",
          "wonka industries", "vandelay industries", "bluth company", "massive dynamic"}
SERVICES = {"tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "hcl",
            "tech mahindra", "mindtree", "mphasis", "genpact", "l&t infotech"}
BIGTECH = {"google", "meta", "amazon", "apple", "netflix", "microsoft", "uber", "airbnb",
           "linkedin", "twitter", "stripe", "nvidia", "openai"}
IN_PRODUCT = {"flipkart", "swiggy", "zomato", "razorpay", "paytm", "ola", "myntra", "cred",
              "phonepe", "meesho", "zerodha", "freshworks", "zoho", "inmobi", "sharechat"}


def _span_months(j) -> int | None:
    sd = str(j.get("start_date") or "")[:7]
    try:
        sy, sm = int(sd[:4]), int(sd[5:7])
    except ValueError:
        return None
    ed = j.get("end_date")
    if ed:
        ed = str(ed)[:7]
        try:
            ey, em = int(ed[:4]), int(ed[5:7])
        except ValueError:
            return None
    else:
        ey, em = REFERENCE_DATE.year, REFERENCE_DATE.month
    return (ey - sy) * 12 + (em - sm)


def extract(c: dict) -> dict:
    prof = c.get("profile") or {}
    career = c.get("career_history") or []
    skills = c.get("skills") or []
    edu = c.get("education") or []
    sig = c.get("redrob_signals") or {}

    yoe = float(prof.get("years_of_experience") or 0)
    summary = str(prof.get("summary") or "")
    m = STATED_YOE.search(summary)
    stated = float(m.group(1)) if m else None

    months = sum(int(j.get("duration_months") or 0) for j in career)
    span_gap = 0
    for j in career:
        span = _span_months(j)
        if span is not None:
            span_gap = max(span_gap, abs(int(j.get("duration_months") or 0) - span))

    def pool_frac(pool):
        if not career:
            return 0.0
        hits = sum(1 for j in career if str(j.get("company") or "").strip().lower() in pool)
        return hits / len(career)

    expert_zero = sum(1 for s in skills
                      if str(s.get("proficiency") or "").lower() == "expert"
                      and int(s.get("duration_months") or 0) == 0)
    tiers = [str(e.get("tier") or "") for e in edu]

    # Generator template signature: summary opening shape with numbers masked.
    opening = re.sub(r"[\d.]+", "#", " ".join(summary.split()[:6])).lower()

    return {
        "candidate_id": c["candidate_id"],
        "yoe_field": yoe,
        "stated_yoe": stated,
        "stated_gap": (yoe - stated) if stated is not None else None,
        "history_months": months,
        "n_roles": len(career),
        "history_gap_months": yoe * 12 - months,
        "span_gap_max": span_gap,
        "frac_sitcom": pool_frac(SITCOM),
        "frac_services": pool_frac(SERVICES),
        "frac_bigtech": pool_frac(BIGTECH),
        "frac_in_product": pool_frac(IN_PRODUCT),
        "expert_zero_count": expert_zero,
        "n_skills": len(skills),
        "edu_tier1": tiers.count("tier_1"),
        "edu_tier2": tiers.count("tier_2"),
        "completeness": float(sig.get("profile_completeness_score") or 0),
        "response_rate": float(sig.get("recruiter_response_rate") or 0),
        "open_to_work": bool(sig.get("open_to_work_flag")),
        "summary_template": opening,
    }


def main() -> None:
    src = ROOT / "candidates.jsonl"
    out = ROOT / "artifacts" / "forensics_features.jsonl"
    out.parent.mkdir(exist_ok=True)

    templates = Counter()
    stated_present = 0
    contradiction = 0  # stated_gap > 3y — the planted-fabrication tell
    by_template_gap = defaultdict(list)
    n = 0

    with src.open("rb") as f, out.open("w", encoding="utf-8") as fh:
        for raw in f:
            if not raw.strip():
                continue
            rec = extract(loads(raw))
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
            templates[rec["summary_template"]] += 1
            if rec["stated_yoe"] is not None:
                stated_present += 1
                by_template_gap[rec["summary_template"]].append(rec["stated_gap"])
                if rec["stated_gap"] is not None and rec["stated_gap"] > 3.0:
                    contradiction += 1
            if n % 20000 == 0:
                print(f"  {n} processed", file=sys.stderr)

    print(f"candidates: {n}")
    print(f"summary self-reports YoE: {stated_present} ({stated_present/n:.1%})")
    print(f"stated-vs-field contradictions (>3y inflation): {contradiction}")
    print(f"distinct summary templates: {len(templates)}")
    print("top 12 templates:")
    for t, cnt in templates.most_common(12):
        gaps = by_template_gap.get(t, [])
        big = sum(1 for g in gaps if g is not None and g > 3)
        print(f"  {cnt:6d}  contradictions={big:5d}  '{t[:60]}'")


if __name__ == "__main__":
    main()
