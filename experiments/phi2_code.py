"""Study Phi-2 -- two-axis coding of the combined corpus (pilot re-mapped + new SE/HN units),
plus a BLINDED second-coder packet and corpus manifest. Single coder (no IRR); the packet +
phi2_kappa.py are ready for a real independent second human coder.
"""
import csv
import hashlib
import json
from pathlib import Path

OUT = Path("docs/human_opinion")

# --- new Phi-2 includable items (two-axis, single-coder reading of REAL retrieved text) ---
# id -> (evidence_status, hiring_action, severity, red_flag_type, role, geo, firsthand, conditional, note)
NEW = {
    "SE_88495": ("AMBIGUOUS", "CONTINUE", 1, "month_or_date_mismatch", "hr_policy_advisor", "unknown", "secondhand", "yes", "minor month gap 3yr ago; 'most employers wouldn't bother checking'"),
    "SE_137241": ("AMBIGUOUS", "CLARIFY", 1, "month_or_date_mismatch", "hr_policy_advisor", "unknown", "secondhand", "no", "resume correct vs bg-check mismatch -> reach out and clarify"),
    "SE_52785": ("CLEAR", "CONTINUE", 1, "minor_formatting_error", "hr_policy_advisor", "unknown", "secondhand", "yes", "'mistakes happen, typos happen, hiring companies understand'"),
    "SE_136842": ("PROBABLE_CONTRADICTION", "BLOCK", 3, "employment_overlap", "hr_policy_advisor", "india", "secondhand", "no", "dual-employment risk -> do not proceed (India relieving/overlap)"),
    "SE_136966": ("PROBABLE_CONTRADICTION", "DOWNRANK", 3, "employment_overlap", "hr_policy_advisor", "india", "secondhand", "no", "dual employment -> don't accept; duration can't be reduced"),
    "SE_30873": ("AMBIGUOUS", "CLARIFY", 2, "employment_overlap", "hr_policy_advisor", "india", "secondhand", "yes", "relieving-date/leave overlap -> finish formalities first (India)"),
    "HN_43628421": ("PROBABLE_CONTRADICTION", "VERIFY", 1, "inflated_skill_duration", "engineer_interviewer", "unknown", "firsthand", "no", "3yr exp claims many tools -> assess awareness of limits, learn on job (ANACHRONISM-relevant)"),
    "HN_35139144": ("AMBIGUOUS", "CONTINUE", 0, "technology_anachronism", "engineer", "unknown", "secondhand", "no", "rejecting on stated years is gameable -> don't gate on claimed tenure (ANACHRONISM-relevant)"),
}
NEW_EXCLUDE = {  # HN anachronism false-positives (tech debates, not hiring decisions)
    "HN_35139487": "child-labor news tangent", "HN_17108123": "kubernetes-vs-bosh tech debate",
    "HN_32214202": "self-describes experience in an argument, no hiring decision",
    "HN_48495500": "LLM cost tangent", "HN_48363436": "who's-hiring India post",
    "HN_40179533": "rust-vs-x debate", "HN_30718758": "golang debate", "HN_29906607": "hardware nostalgia",
    "HN_28462589": "nomad tooling", "HN_27743544": "k8s tooling", "HN_9017334": "ruby learning anecdote",
    "HN_7770303": "internal-tooling anecdote", "HN_7695566": "slide-to-unlock tangent",
    "HN_7132039": "rails rant", "HN_5200939": "REPL history", "HN_46526041": "rails hype",
    "HN_46485812": "AI-summary of unrelated thread", "HN_40018783": "unit-test debate",
    "HN_39311900": "event-bus debate", "HN_39131572": "consciousness tangent",
    "HN_38587116": "JVM perf debate", "HN_35536599": "go-vs-java preference",
}

V1_ACTION_TO_V2 = {"ignore": "CONTINUE", "continue_interview": "CONTINUE", "work_sample": "CONTINUE",
                   "lower_confidence": "DOWNRANK", "ask_for_explanation": "CLARIFY",
                   "technical_verification": "VERIFY", "background_check": "VERIFY",
                   "reference_check": "VERIFY", "reject": "BLOCK", "blacklist_or_escalate": "BLOCK"}


def sev_to_evidence(s):
    return ["CLEAR", "AMBIGUOUS", "PROBABLE_CONTRADICTION", "PROBABLE_CONTRADICTION", "CONFIRMED_CONTRADICTION"][int(s)]


def main():
    raw2 = {json.loads(l)["item_id"]: json.loads(l) for l in open(OUT / "raw_phi2_corpus.jsonl", encoding="utf-8")}
    pilot = list(csv.DictReader(open(OUT / "corpus_pilot.csv", encoding="utf-8")))

    cols = ["item_id", "platform", "thread_id", "source_date", "query_family", "stratum",
            "author_claimed_role", "geography", "red_flag_type", "severity",
            "evidence_status", "hiring_action", "firsthand_or_secondhand", "conditional_reasoning",
            "source_url", "coder_1", "coder_2", "adjudicated", "notes"]
    rows = []
    # re-map pilot (HN) to two-axis
    for r in pilot:
        sev = int(r["severity"])
        ev = sev_to_evidence(sev); act = V1_ACTION_TO_V2.get(r["recommended_action"], "CLARIFY")
        rows.append({"item_id": r["item_id"], "platform": r["platform"], "thread_id": r["thread_id"],
                     "source_date": r["source_date"], "query_family": r["query_family"], "stratum": "hackernews",
                     "author_claimed_role": r["author_claimed_role"], "geography": r["geography"],
                     "red_flag_type": r["red_flag_type"], "severity": sev, "evidence_status": ev,
                     "hiring_action": act, "firsthand_or_secondhand": r["firsthand_or_secondhand"],
                     "conditional_reasoning": r["conditional_reasoning"], "source_url": r["source_url"],
                     "coder_1": f"{ev}|{act}|sev{sev}", "coder_2": "AWAITING_SECOND_CODER",
                     "adjudicated": "", "notes": "pilot, re-mapped v1->v2"})
    # new units
    for iid, c in NEW.items():
        if iid not in raw2:
            continue
        r = raw2[iid]; ev, act, sev, typ, role, geo, fh, cond, note = c
        strat = "workplace_se" if r["platform"].startswith("workplace") else "hackernews"
        rows.append({"item_id": iid, "platform": r["platform"], "thread_id": r["thread_id"],
                     "source_date": r["source_date"], "query_family": r["query_family"], "stratum": strat,
                     "author_claimed_role": role, "geography": geo, "red_flag_type": typ, "severity": sev,
                     "evidence_status": ev, "hiring_action": act, "firsthand_or_secondhand": fh,
                     "conditional_reasoning": cond, "source_url": r["source_url"],
                     "coder_1": f"{ev}|{act}|sev{sev}", "coder_2": "AWAITING_SECOND_CODER",
                     "adjudicated": "", "notes": note})
    with open(OUT / "corpus_phi2.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    # blinded second-coder packet: de-identified rows, NO coder_1 labels, with excerpt for coding
    raw_all = {**{r["item_id"]: r for r in
                  [json.loads(l) for l in open(OUT / "raw_hn_corpus.jsonl", encoding="utf-8")]}, **raw2}
    with open(OUT / "second_coder_packet.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            src = raw_all.get(r["item_id"], {})
            f.write(json.dumps({"item_id": r["item_id"], "stratum": r["stratum"],
                                "excerpt": (src.get("text") or "")[:700],
                                "source_url": r["source_url"],
                                "evidence_status": None, "hiring_action": None, "severity": None,
                                "red_flag_type": None}) + "\n")

    # exclusion log append (phi2 false positives)
    with open(OUT / "exclusion_log_phi2.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["item_id", "reason_excluded"])
        for iid, reason in NEW_EXCLUDE.items():
            w.writerow([iid, reason])

    from collections import Counter
    anach = sum(1 for r in rows if r["red_flag_type"] in ("technology_anachronism", "inflated_skill_duration"))
    manifest = {"study": "Phi-2", "combined_units": len(rows),
                "strata": dict(Counter(r["stratum"] for r in rows)),
                "new_included": len(NEW), "new_excluded": len(NEW_EXCLUDE),
                "anachronism_decision_items": anach, "anachronism_saturation_reached": anach >= 20,
                "second_coder": "AWAITING (packet de-identified, no coder_1 labels)",
                "frozen_hash": hashlib.sha256("|".join(sorted(r["item_id"] for r in rows)).encode()).hexdigest()[:16]}
    json.dump(manifest, open(OUT / "corpus_phi2_manifest.json", "w"), indent=2)
    print(f"combined corpus: {len(rows)} units  strata={manifest['strata']}")
    print(f"anachronism-decision items: {anach} (saturation>=20: {manifest['anachronism_saturation_reached']})")
    print(f"hash {manifest['frozen_hash']}; second-coder packet de-identified & ready")


if __name__ == "__main__":
    main()
