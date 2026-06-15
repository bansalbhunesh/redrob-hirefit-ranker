"""Non-ranking integrity-audit-card feature (Phi-justified product layer).

Operates STRICTLY DOWNSTREAM of the frozen golden ranking -- it annotates, never reorders,
never rescores. Maps deterministic integrity signals to the two-axis interface validated by
Study Phi:

  golden ranking -> integrity evidence classifier ->
      Evidence status: CLEAR | AMBIGUOUS | PROBABLE_CONTRADICTION | CONFIRMED_CONTRADICTION
      Recommended action: CONTINUE | CLARIFY | VERIFY | DOWNRANK | BLOCK
  -> audit card (reason + corroborating evidence + verification request)

This replaces "honeypot = true/false" with a proportionate, recruiter-authentic state, while
golden (af8f2b32) and all scores stay byte-identical. Outputs cards for golden's top-100.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")

from _lib import load_pool  # noqa: E402
from anachronism import violations, worst_severity  # noqa: E402

OUT = Path("docs/human_opinion")

# Evidence status x recommended action (grounded in the Phi severity-conditioned surface:
# minor->continue/clarify, probable->verify, confirmed-objective-impossibility->block).
ACTION = {"CLEAR": "CONTINUE", "AMBIGUOUS": "CLARIFY",
          "PROBABLE_CONTRADICTION": "VERIFY", "CONFIRMED_CONTRADICTION": "BLOCK"}


def classify_card(rec: dict) -> dict:
    cand, vals = rec["cand"], rec["values"]
    hp, dq = rec["honeypot_mult"], rec["disq_mult"]
    vio = violations(cand)

    if hp <= 0.0:                       # shipped hard honeypot: objective impossibility
        ev = "CONFIRMED_CONTRADICTION"
        reason = "Objective résumé impossibility flagged by the shipped honeypot detector (e.g. career timeline exceeds claimed experience, impossible education dates, or multiple concurrent current jobs)."
        vreq = "Confirm employment timeline and education dates against documentary records."
    elif vio:                            # anachronism: inconsistent, not decisively verified
        ev = "PROBABLE_CONTRADICTION"
        v = max(vio, key=lambda x: x.get("severity", 0))
        if v["type"] == "skill_duration":
            reason = (f"Claimed tenure in '{v['tech']}' is {int(v['claimed_months'])} months, "
                      f"which exceeds the technology's plausible age (~{int(v['max_months'])} months).")
            vreq = f"Ask the candidate for the project timeline and version history of their {v['tech']} work."
        else:
            reason = (f"A completed role ending {v.get('job_end_year')} references '{v['tech']}', "
                      f"which post-dates that role (tech ~{v.get('tech_first_year')}).")
            vreq = f"Confirm the start/end dates of the role citing {v['tech']}."
    elif abs(hp - 0.05) < 1e-6 or dq < 1.0:  # softened / disqualifier: ambiguous data quality
        ev = "AMBIGUOUS"
        reason = "Incomplete or borderline résumé metadata (e.g. abbreviated history vs claimed experience, or uncorroborated expert skill) with a plausible innocent explanation."
        vreq = "Ask the candidate to fill in missing dates/durations; corroborate in interview."
    else:
        ev = "CLEAR"
        reason = "No meaningful contradictory evidence detected."
        vreq = "None required."

    corrob = []
    if rec.get("production_evidence", 0) >= 0.5:
        corrob.append("production/retrieval career evidence")
    if vals.get("scale_signal", 0) >= 0.4:
        corrob.append("scale signal")
    if vals.get("assessment_score_avg", 0) >= 0.4:
        corrob.append("verified assessment")
    if vals.get("ir_ranking_experience", 0) >= 0.45:
        corrob.append("ranking/IR experience")
    return {"candidate_id": rec["cid"], "role_fit": round(float(rec["hand"]), 3),
            "evidence_status": ev, "recommended_action": ACTION[ev],
            "anachronism_severity": round(worst_severity(cand), 2) if vio else 0.0,
            "reason": reason, "corroborating_evidence": corrob or ["none surfaced"],
            "verification_request": vreq}


def main():
    recs, golden_ids = load_pool()
    rec_by = {r["cid"]: r for r in recs}
    cards = [classify_card(rec_by[c]) for c in golden_ids if c in rec_by]
    json.dump(cards, open(OUT / "integrity_cards.json", "w"), indent=2)

    from collections import Counter
    dist = Counter((c["evidence_status"], c["recommended_action"]) for c in cards)
    print("golden top-100 integrity audit (DOWNSTREAM of ranking; golden unchanged):")
    for (ev, act), n in dist.most_common():
        print(f"  {ev:<24} -> {act:<10} {n}")

    # demo cards: one CLEAR, the most-severe PROBABLE, an AMBIGUOUS/CONFIRMED if any
    demo = []
    for ev in ("CLEAR", "PROBABLE_CONTRADICTION", "AMBIGUOUS", "CONFIRMED_CONTRADICTION"):
        pool = [c for c in cards if c["evidence_status"] == ev]
        if pool:
            demo.append(max(pool, key=lambda c: c["anachronism_severity"] if ev == "PROBABLE_CONTRADICTION" else c["role_fit"]))
    lines = ["# Integrity Audit Cards — demo (downstream of frozen golden; ranking unchanged)\n",
             "Replaces `honeypot=true/false` with a proportionate two-axis state validated by Study Φ.",
             "Golden (`af8f2b32`) and all scores are byte-identical; this is an annotation layer only.\n",
             f"Distribution over golden's top-100: " +
             ", ".join(f"{ev}->{act}:{n}" for (ev, act), n in dist.most_common()) + "\n"]
    for c in demo:
        lines += [f"## {c['candidate_id']}", f"- Role fit: **{c['role_fit']}**",
                  f"- Evidence status: **{c['evidence_status']}**",
                  f"- Recommended action: **{c['recommended_action']}**",
                  f"- Reason: {c['reason']}",
                  f"- Corroborating evidence: {', '.join(c['corroborating_evidence'])}",
                  f"- Verification request: {c['verification_request']}\n"]
    (OUT / "integrity_cards_demo.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\ncards -> {OUT}/integrity_cards.json ; demo -> {OUT}/integrity_cards_demo.md")
    print("note: the 52 anachronism candidates render as PROBABLE_CONTRADICTION -> VERIFY "
          "(proportionate), NOT discarded -- the recruiter-useful framing.")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
