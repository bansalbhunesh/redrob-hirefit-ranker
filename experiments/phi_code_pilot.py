"""Study Phi -- SINGLE-CODER pilot coding of the real retrieved HN corpus.

These codes are ONE coder's reading of REAL retrieved comments (text in
docs/human_opinion/raw_hn_corpus.jsonl, URLs preserved). Intercoder reliability is NOT
established (no second human coder available) -> treat as a pilot that establishes the
METHOD and a first severity-action surface, not a publishable distribution. Writes
corpus_pilot.csv, inclusion_log.csv, exclusion_log.csv, corpus_manifest.json.
"""
import csv
import hashlib
import json
from pathlib import Path

OUT = Path("docs/human_opinion")
RAW = OUT / "raw_hn_corpus.jsonl"

# item_id -> (stance, type, severity, action, comp_evidence, role, geo, seniority,
#             firsthand, conditional, note)
CODES = {
    "HN_5924518": ("VERIFY_FIRST", "inflated_skill_duration", 2, "technical_verification", "technical_interview", "engineer", "us", "any", "secondhand", "no", "20yr C++ but fails basics -> interview catches it"),
    "HN_6876400": ("INTEGRITY_HIGH", "fabricated_employment", 3, "reject", "none", "engineer_selfclaimed", "india", "any", "firsthand", "no", "claims lying common; PREJUDICED framing, recorded as stated"),
    "HN_4299160": ("QUALITY_FIRST", "none", 0, "work_sample", "work_sample", "founder", "us", "any", "secondhand", "no", "work-sample test over 'experience preferred'"),
    "HN_43863812": ("VERIFY_FIRST", "fabricated_employment", 2, "background_check", "consistent_external_history", "engineer", "eu", "any", "firsthand", "no", "third-party check: education+employment real-or-fake"),
    "HN_32999283": ("VERIFY_FIRST", "identity_or_proxy_candidate_fraud", 3, "background_check", "references", "hiring_mgr_selfclaimed", "us", "any", "secondhand", "no", "verify employment + photo ID before offer"),
    "HN_3042064": ("VERIFY_FIRST", "fabricated_qualification", 2, "background_check", "consistent_external_history", "recruiter_selfclaimed", "us", "any", "firsthand", "no", "ran recruiting; fake LinkedIn; companies run checks"),
    "HN_36887266": ("INTEGRITY_HIGH", "identity_or_proxy_candidate_fraud", 4, "technical_verification", "technical_interview", "founder_selfclaimed", "us", "any", "firsthand", "no", "post-AI: hundreds of fake/ChatGPT applicants"),
    "HN_5806630": ("QUALITY_FIRST", "none", 0, "work_sample", "work_sample", "engineer", "us", "any", "secondhand", "no", "resume->interview->work a week to judge"),
    "HN_4562445": ("INTEGRITY_HIGH", "fabricated_employment", 3, "background_check", "consistent_external_history", "recruiter_selfclaimed", "us", "any", "firsthand", "no", "did background checks for years; a lie usually -> reject"),
    "HN_2764115": ("QUALITY_FIRST", "none", 0, "continue_interview", "career_description", "hiring_mgr_selfclaimed", "us", "any", "firsthand", "no", "claims can read engineer quality from resume"),
    "HN_22228664": ("QUALITY_FIRST", "none", 0, "work_sample", "work_sample", "founder_selfclaimed", "us", "any", "firsthand", "no", "resumes/whiteboards bad predictors; week-long project"),
    "HN_5442892": ("QUALITY_FIRST", "none", 0, "continue_interview", "github_or_portfolio", "engineer", "us", "any", "secondhand", "no", "hire on portfolio of authored projects"),
    "HN_5070918": ("QUALITY_FIRST", "inflated_skill_duration", 1, "ignore", "technical_interview", "engineer", "us", "any", "secondhand", "no", "good engineer works blind on new tech; tenure not required (ANACHRONISM-relevant)"),
    "HN_39412664": ("QUALITY_FIRST", "none", 0, "continue_interview", "technical_interview", "hiring_mgr_selfclaimed", "us", "any", "firsthand", "no", "find great candidates who interview poorly / bad resumes"),
    "HN_39744453": ("CONTEXT_DEPENDENT", "none", 0, "continue_interview", "career_description", "engineer", "us", "any", "secondhand", "yes", "experience-vs-projects weight 'depends on company, role'"),
    "HN_2246385": ("INTEGRITY_HIGH", "minor_formatting_error", 1, "reject", "none", "hiring_mgr_selfclaimed", "us", "any", "firsthand", "no", "disregarded resumes for a single typo (strict outlier)"),
    "HN_35398004": ("QUALITY_FIRST", "inflated_responsibility", 1, "ignore", "technical_interview", "hiring_mgr_selfclaimed", "us", "any", "firsthand", "no", "would ignore inflated CV statements; may hurt candidate"),
    "HN_35240702": ("QUALITY_FIRST", "technology_anachronism", 0, "ignore", "technical_interview", "engineer", "us", "any", "secondhand", "no", "skilled devs learn new lang fast even unplanned (ANACHRONISM-relevant)"),
    "HN_19062949": ("QUALITY_FIRST", "fabricated_qualification", 1, "technical_verification", "technical_interview", "ops_engineer_selfclaimed", "us", "any", "firsthand", "no", "certifications moot; capability over credential"),
    "HN_39744453b": None,  # placeholder guard (unused)
}
CODES.pop("HN_39744453b", None)

# excluded items reviewed (id -> reason)
EXCLUDED = {
    "HN_4315201": "personal anecdote, no hiring decision/rule",
    "HN_44202622": "macro job-market commentary, not a candidate decision",
    "HN_47221274": "who's-hiring location/skills post",
    "HN_47320624": "who's-hiring location/skills post",
    "HN_48117207": "who's-hiring location/skills post",
    "HN_47988965": "self-intro, no integrity decision",
    "HN_8543588": "company ad (who's hiring)",
    "HN_18592018": "job posting",
    "HN_40900565": "resume-tailoring/ATS advice",
    "HN_48442301": "interview-screening complaint, no integrity rule",
    "HN_28979413": "personal job-search anecdote, no rule",
    "HN_16043772": "tech-hype debate, not candidate integrity",
    "HN_42854135": "LLM/tech tangent",
    "HN_48495500": "LLM model-cost tangent",
    "HN_46124771": "seniority-market commentary, no candidate decision",
    "HN_1025490": "off-topic (gender/workplace)",
    "HN_22376651": "off-topic (platform moderation)",
}


def main():
    raw = {json.loads(l)["item_id"]: json.loads(l) for l in open(RAW, encoding="utf-8")}
    cols = ["item_id", "platform", "thread_id", "source_date", "query_family", "author_hash",
            "author_claimed_role", "author_role_confidence", "geography", "candidate_seniority",
            "red_flag_type", "severity", "stance", "recommended_action", "compensating_evidence",
            "firsthand_or_secondhand", "conditional_reasoning", "brief_excerpt", "source_url",
            "coder_1", "coder_2", "adjudicated_code", "notes"]
    rows = []
    for iid, c in CODES.items():
        if iid not in raw:
            continue
        r = raw[iid]
        stance, typ, sev, action, comp, role, geo, sen, fh, cond, note = c
        rows.append({
            "item_id": iid, "platform": "hackernews", "thread_id": r["thread_id"],
            "source_date": r["source_date"], "query_family": r["query_family"],
            "author_hash": r["author_hash"], "author_claimed_role": role,
            "author_role_confidence": "self_claimed", "geography": geo, "candidate_seniority": sen,
            "red_flag_type": typ, "severity": sev, "stance": stance, "recommended_action": action,
            "compensating_evidence": comp, "firsthand_or_secondhand": fh,
            "conditional_reasoning": cond, "brief_excerpt": r["text"][:180],
            "source_url": r["source_url"], "coder_1": f"{stance}|{action}|sev{sev}",
            "coder_2": "AWAITING_SECOND_CODER", "adjudicated_code": "", "notes": note})
    with open(OUT / "corpus_pilot.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    with open(OUT / "inclusion_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["item_id", "reason_included"])
        for r in rows:
            w.writerow([r["item_id"], "clear hiring judgment on resume truth/evidence w/ reasoning"])
    with open(OUT / "exclusion_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["item_id", "reason_excluded"])
        for iid, reason in EXCLUDED.items():
            w.writerow([iid, reason])
    manifest = {"study": "Phi pilot", "stratum": "hackernews_only", "coder": "single (no IRR)",
                "retrieved_total": len(raw), "coded_included": len(rows),
                "reviewed_excluded": len(EXCLUDED),
                "remaining_uncoded": len(raw) - len(rows) - len(EXCLUDED),
                "frozen_hash": hashlib.sha256("|".join(sorted(CODES)).encode()).hexdigest()[:16]}
    json.dump(manifest, open(OUT / "corpus_manifest.json", "w"), indent=2)
    print(f"coded (single-coder pilot): {len(rows)} included, {len(EXCLUDED)} reviewed-excluded, "
          f"{manifest['remaining_uncoded']} uncoded of {len(raw)} retrieved")
    print(f"manifest hash {manifest['frozen_hash']}; corpus -> {OUT}/corpus_pilot.csv")


if __name__ == "__main__":
    main()
