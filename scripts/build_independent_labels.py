#!/usr/bin/env python3
"""Independent relevance labels for de-circularised local evaluation.

WHY THIS EXISTS
---------------
`scripts/build_silver_labels.py` derives labels from the SAME `compute_features`
the ranker uses, so evaluating the ranker against them measures self-consistency,
not fit to the hidden ground truth. This module is a *separate* judge: it shares
no code with `redrob_ranker.features`, reads raw candidate fields directly, and
applies a narrative-first rubric grounded in the JD. It deliberately weights
career-story evidence and seniority more than skill-keyword lists, so that
agreement with the ranker is meaningful and disagreement is a real signal.

It is still a HEURISTIC proxy. The gold path is `scripts/llm_judge_labels.py`
(LLM-judged tiers on a stratified sample). Use this for fast, full-pool A/B
testing of ranker changes; use the LLM labels to anchor the heuristic.

Tiers (0 worst .. 5 best) mirror the challenge's graded relevance.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

REFERENCE_DATE = date(2026, 6, 8)
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-\d{2}$")

# --- Independent vocabularies (intentionally NOT imported from the ranker) ---
TARGET_ROLE = re.compile(
    r"(machine learning|ml engineer|ai engineer|applied scientist|applied ml|"
    r"nlp engineer|search engineer|recommendation|recsys|information retrieval|"
    r"data scientist|research engineer|relevance|ranking)", re.I)
SENIOR = re.compile(r"(senior|staff|lead|principal|head)", re.I)
BUILT_SYSTEMS = re.compile(
    r"(recommend|ranking|retrieval|search relevance|semantic search|vector|"
    r"embedding|matching engine|personali|nearest neighbor|learning to rank|"
    r"recsys|information retrieval|relevance)", re.I)
PRODUCTION = re.compile(
    r"(shipped|deployed|in production|production|launched|served|serving|"
    r"latency|throughput|real[- ]time|a/b|millions?|scale|users)", re.I)
WRAPPER_ONLY = re.compile(r"(langchain|llama[- ]?index|prompt engineering|chatgpt|gpt-?4 api)", re.I)
RESEARCH_ONLY = re.compile(r"(research lab|postdoc|professor|phd thesis|dissertation|arxiv|publication)", re.I)
CV_SPEECH = re.compile(r"(image classification|computer vision|opencv|speech recognition|text to speech|robotics|gan)", re.I)
SERVICES = re.compile(r"(tcs|infosys|wipro|accenture|cognizant|capgemini|mindtree|hcl|tech mahindra)", re.I)
NON_TARGET = re.compile(r"(marketing manager|hr manager|accountant|graphic designer|content writer|"
                        r"sales executive|customer support|operations manager|mechanical engineer|civil engineer)", re.I)
INDIA_PREF = re.compile(r"(pune|noida|delhi|ncr|gurgaon|gurugram|mumbai|hyderabad|bangalore|bengaluru)", re.I)


def _days_since(s):
    if not s:
        return 9999
    try:
        y, m, d = (int(x) for x in str(s)[:10].split("-"))
        return max(0, (REFERENCE_DATE - date(y, m, d)).days)
    except Exception:
        return 9999


def _is_honeypot(c: dict) -> bool:
    """Independent impossible-profile detector (structural contradictions only)."""
    prof = c.get("profile", {})
    career = c.get("career_history", []) or []
    yoe = float(prof.get("years_of_experience") or 0)
    career_months = sum(int(j.get("duration_months") or 0) for j in career)
    if yoe and career_months > yoe * 12 + 30:
        return True
    if yoe >= 5 and career and career_months < yoe * 12 * 0.45:
        return True
    expert_zero = sum(1 for s in c.get("skills", []) or []
                      if str(s.get("proficiency", "")).lower() == "expert"
                      and int(s.get("duration_months") or 0) == 0)
    if expert_zero >= 2:
        return True
    for j in career:
        if j.get("is_current") and j.get("end_date"):
            return True
        sd, ed, dm = str(j.get("start_date") or "")[:10], j.get("end_date"), int(j.get("duration_months") or 0)
        start = DATE_RE.match(sd)
        if not start:
            continue
        sy, sm = int(start.group(1)), int(start.group(2))
        if ed:
            end = DATE_RE.match(str(ed)[:10])
            if not end:
                continue
            ey, em = int(end.group(1)), int(end.group(2))
            span = (ey - sy) * 12 + (em - sm)
        else:
            span = (REFERENCE_DATE.year - sy) * 12 + (REFERENCE_DATE.month - sm)
        if dm - span > 2:
            return True
    return False


MAX_POINTS = 8.0  # theoretical max of the additive evidence below


def label_candidate(c: dict) -> tuple[int, float, list[str]]:
    """Return (tier 0..5 int, continuous relevance 0..5 float, reasons).

    The continuous relevance preserves within-tier ordering so NDCG can
    discriminate among strong candidates (where NDCG@10 is actually decided);
    the integer tier is used for the binary P@10 / MAP definitions.
    """
    prof = c.get("profile", {})
    sig = c.get("redrob_signals", {})
    career = c.get("career_history", []) or []

    if _is_honeypot(c):
        return 0, 0.0, ["honeypot_impossible"]

    title = str(prof.get("current_title") or "")
    hist_titles = " ".join(str(j.get("title") or "") for j in career)
    career_text = " ".join(str(j.get("description") or "") for j in career)
    summary = str(prof.get("summary") or "")
    blob = f"{title} {hist_titles} {summary} {career_text}"

    reasons = []
    # Hard JD exclusions: non-target current role with no ML history at all.
    if NON_TARGET.search(title) and not TARGET_ROLE.search(blob):
        return 0, 0.0, ["non_target_role_no_ml"]

    pts = 0.0
    if TARGET_ROLE.search(title):
        pts += 2.0; reasons.append("target_title")
    elif TARGET_ROLE.search(hist_titles):
        pts += 1.0; reasons.append("ml_history")
    if SENIOR.search(title):
        pts += 0.5; reasons.append("senior")

    built = len(set(m.group(0).lower() for m in BUILT_SYSTEMS.finditer(career_text)))
    if built >= 2:
        pts += 2.0; reasons.append("built_retrieval_ranking")
    elif built == 1:
        pts += 1.0; reasons.append("some_systems_evidence")
    if PRODUCTION.search(career_text):
        pts += 1.0; reasons.append("production_evidence")

    yoe = float(prof.get("years_of_experience") or 0)
    if 5 <= yoe <= 9:
        pts += 1.0; reasons.append("yoe_in_band")
    elif yoe < 4:
        pts -= 1.0; reasons.append("too_junior")
    elif yoe > 11:
        pts -= 0.5; reasons.append("over_band")

    # availability / reachability (narrative judge keeps this modest)
    rr = float(sig.get("recruiter_response_rate") or 0)
    if rr >= 0.5 and _days_since(sig.get("last_active_date")) <= 60 and sig.get("open_to_work_flag"):
        pts += 1.0; reasons.append("reachable")
    elif rr < 0.2 or _days_since(sig.get("last_active_date")) > 150:
        pts -= 1.0; reasons.append("hard_to_reach")
    if INDIA_PREF.search(str(prof.get("location") or "")):
        pts += 0.5; reasons.append("preferred_location")

    # JD disqualifiers (independent)
    if RESEARCH_ONLY.search(blob) and not PRODUCTION.search(career_text):
        pts -= 2.0; reasons.append("research_no_deploy")
    if len(CV_SPEECH.findall(blob)) >= 2 and not BUILT_SYSTEMS.search(career_text):
        pts -= 1.5; reasons.append("cv_speech_primary")
    if WRAPPER_ONLY.search(blob) and built == 0 and yoe < 6:
        pts -= 1.5; reasons.append("langchain_wrapper_only")
    cur_company = str((career[0].get("company") if career else "") or prof.get("current_company") or "")
    if SERVICES.search(cur_company) and not any(BUILT_SYSTEMS.search(str(j.get("description") or "")) for j in career):
        pts -= 1.0; reasons.append("services_no_product")

    # map points -> integer tier (for binary P@10/MAP) and continuous relevance
    # (0..5 float, for graded NDCG ordering within the strong tier).
    tier = max(0, min(5, round(pts)))
    relevance = max(0.0, min(5.0, pts / MAX_POINTS * 5.0))
    return tier, relevance, reasons or ["adjacent"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Build independent (non-circular) relevance labels.")
    ap.add_argument("--candidates", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--max-candidates", type=int, default=None)
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    dist = [0, 0, 0, 0, 0, 0]
    with args.out.open("w", encoding="utf-8") as fh:
        for line in open(args.candidates, "r", encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            tier, relevance, reasons = label_candidate(c)
            dist[tier] += 1
            fh.write(json.dumps({"candidate_id": c["candidate_id"], "tier": tier,
                                 "relevance": round(relevance, 4), "reasons": reasons}) + "\n")
            n += 1
            if args.max_candidates and n >= args.max_candidates:
                break
    print(f"Wrote {n} independent labels to {args.out}")
    print("tier distribution 0..5:", dist)


if __name__ == "__main__":
    main()
