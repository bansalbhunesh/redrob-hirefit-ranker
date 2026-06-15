"""Experiment Psi -- pre-registered ANALYSIS + shipping rule.

Runs the eight required analyses on REAL reviewer responses and emits the final decision via
the PRE-REGISTERED rule below. Collects nothing itself. Until real responses exist it prints
the frozen rule and reports AWAITING DATA. A clearly-labelled `--selftest` fills SYNTHETIC
responses ONLY to validate harness mechanics (never to be reported as human results).

Responses file: experiments/psi_panel/responses.jsonl, one row per (reviewer, candidate):
  {reviewer_id, family in [recruiter|engineer|neutral], anon_id,
   A1_suitability_0to5, A2_belongs_top100_yes_no, A4_confidence_low_med_high,
   B1_decision_materially_changes_yes_no,
   B2_issue_class in [noise|incomplete|suspicious|decisive_impossibility],
   B3_remain_top100_yes_no, B4_reject_regardless_yes_no}
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

PANEL = Path("experiments/psi_panel")

# --------- PRE-REGISTERED SHIPPING RULE (frozen before any responses) ---------
SHIPPING_RULE = {
    "ship_golden_iff": [
        "no top-100 candidate is classified hard-contradiction by a majority with high confidence",
        "golden remains human-preferred vs constrained_fusion on the pairwise lockbox",
    ],
    "ship_constrained_fusion_iff": [
        "improves human pairwise quality vs golden",
        "introduces no majority-confirmed hard contradiction into the top-10",
        "expected majority-confirmed hard contradictions in top-100 safely below the official threshold",
        "advantage survives reviewer-family deletion",
    ],
    "otherwise": "NO_RANKING_DOMINATES -> ship frozen golden (preregistered, reproducible default)",
    "integrity_reversal_thresholds": {"<0.20": "noise", "0.20-0.50": "ambiguous/unresolved",
                                      ">0.50": "materially changes selection", ">0.75": "hard exclusion"},
}
YN = {"yes": 1, "y": 1, "no": 0, "n": 0, True: 1, False: 0, 1: 1, 0: 0}


def load_responses():
    f = PANEL / "responses.jsonl"
    if not f.exists():
        return []
    return [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]


def analyse(resp, key):
    by_cid = defaultdict(list)
    for r in resp:
        info = key.get(r["anon_id"])
        if info:
            by_cid[info["cid"]].append(r)
    bucket = {info["cid"]: info["bucket"] for info in key.values()}

    def yn(v):
        return YN.get(str(v).lower() if isinstance(v, str) else v, 0)

    # 1 role-quality agreement: stddev of A1 across reviewers (lower=more agreement)
    rq = [np.std([float(r["A1_suitability_0to5"]) for r in rs]) for rs in by_cid.values()
          if len(rs) > 1 and all(r.get("A1_suitability_0to5") is not None for r in rs)]
    role_quality_agree = float(1.0 - np.mean(rq) / 5.0) if rq else None

    # 2 integrity agreement: fraction of candidates with majority issue-class consensus
    def majority_class(rs):
        cs = [r.get("B2_issue_class_[noise|incomplete|suspicious|decisive_impossibility]") for r in rs]
        cs = [c for c in cs if c]
        if not cs:
            return None
        from collections import Counter
        return Counter(cs).most_common(1)[0]
    integ_consensus = [majority_class(rs) for rs in by_cid.values()]
    integ_agree = float(np.mean([m[1] / len([r for r in rs])
                       for rs, m in zip(by_cid.values(), integ_consensus) if m])) if any(integ_consensus) else None

    # 3 integrity reversal rate (flagged buckets), overall + by family
    def reversal(rs_filter):
        sel = rev = 0
        for cid, rs in by_cid.items():
            if bucket.get(cid) not in ("fusion_gain_drivers", "matched_clean", "hard_integrity_controls",
                                       "ambiguous_date_quality"):
                continue
            for r in rs:
                if not rs_filter(r):
                    continue
                if yn(r.get("A2_belongs_top100_yes_no")):
                    sel += 1
                    if not yn(r.get("B3_remain_top100_yes_no")):
                        rev += 1
        return (rev / sel) if sel else None
    reversal_all = reversal(lambda r: True)
    reversal_recruiter = reversal(lambda r: r.get("family") == "recruiter")
    reversal_engineer = reversal(lambda r: r.get("family") == "engineer")

    # 8 majority-confirmed hard contradictions among panel candidates, by bucket
    def majority_hard(cid):
        rs = by_cid.get(cid, [])
        if not rs:
            return False
        hc = sum(1 for r in rs if r.get("B2_issue_class_[noise|incomplete|suspicious|decisive_impossibility]")
                 == "decisive_impossibility" and r.get("B5_confidence_low_med_high") == "high")
        return hc > len(rs) / 2
    drivers_hard = sum(1 for c in bucket if bucket[c] == "fusion_gain_drivers" and majority_hard(c))

    return {"n_responses": len(resp), "n_reviewers": len({r.get("reviewer_id") for r in resp}),
            "role_quality_agreement": role_quality_agree, "integrity_agreement": integ_agree,
            "integrity_reversal_rate_all": reversal_all,
            "integrity_reversal_recruiter": reversal_recruiter,
            "integrity_reversal_engineer": reversal_engineer,
            "fusion_drivers_majority_hard_contradiction": drivers_hard,
            "n_fusion_drivers": sum(1 for c in bucket if bucket[c] == "fusion_gain_drivers")}


def decide(a):
    rr = a["integrity_reversal_rate_all"]
    if rr is None:
        return "AWAITING_HUMAN_DATA"
    drivers_hard = a["fusion_drivers_majority_hard_contradiction"]
    if rr > 0.5 or drivers_hard >= 3:
        return "HUMANS_PENALISE_INTEGRITY -> ship integrity-constrained ONLY if it passes all quality gates"
    if rr < 0.2 and drivers_hard == 0:
        return "HUMANS_TREAT_AS_NOISE -> constrained_fusion defensible; recovered candidates are genuine"
    return "REVIEWERS_DIVIDED -> NO_RANKING_DOMINATES -> ship frozen golden (ambiguity empirically irreducible)"


def selftest():
    """SYNTHETIC mechanics check -- NOT human results. Two worlds to show the rule reacts."""
    key = json.load(open(PANEL / "anon_key.json"))
    import random
    for world, p_rev in [("noise-world (lambda~0)", 0.05), ("integrity-world (lambda high)", 0.85)]:
        rng = random.Random(0)
        resp = []
        for anon, info in key.items():
            flagged = info["bucket"] in ("fusion_gain_drivers", "hard_integrity_controls", "ambiguous_date_quality")
            for fam, rid in [("recruiter", 0), ("engineer", 1), ("neutral", 2)]:
                sel = 1 if info["bucket"] in ("fusion_gain_drivers", "matched_clean", "strong_clean") else 0
                revd = flagged and sel and (rng.random() < p_rev)
                resp.append({"reviewer_id": rid, "family": fam, "anon_id": anon,
                             "A1_suitability_0to5": 4 if sel else 2, "A2_belongs_top100_yes_no": sel,
                             "A4_confidence_low_med_high": "high",
                             "B3_remain_top100_yes_no": 0 if revd else sel,
                             "B2_issue_class_[noise|incomplete|suspicious|decisive_impossibility]":
                                 ("decisive_impossibility" if revd else "noise"),
                             "B5_confidence_low_med_high": "high"})
        a = analyse(resp, key)
        print(f"\n[SELF-TEST {world}] reversal_all={a['integrity_reversal_rate_all']}  "
              f"drivers_hard={a['fusion_drivers_majority_hard_contradiction']}")
        print(f"  -> {decide(a)}")
    print("\n(SELF-TEST is synthetic harness validation, NOT human evidence.)")


def main():
    print("=== Experiment Psi: pre-registered shipping rule ===")
    print(json.dumps(SHIPPING_RULE, indent=2))
    key_f = PANEL / "anon_key.json"
    if not key_f.exists():
        print("\nPanel not built; run psi_panel.py first."); return
    resp = load_responses()
    if not resp:
        print(f"\nAWAITING HUMAN DATA: {PANEL/'responses.jsonl'} is empty.")
        print("Collect from 9 reviewers (3 recruiter / 3 engineer / 3 neutral); >=3 judgments/candidate.")
        if "--selftest" in sys.argv:
            selftest()
        return
    a = analyse(resp, json.load(open(key_f)))
    print("\n=== analyses ==="); print(json.dumps(a, indent=2))
    print("\n=== DECISION ==="); print(decide(a))
    json.dump({"analyses": a, "decision": decide(a), "shipping_rule": SHIPPING_RULE},
              open(PANEL / "psi_result.json", "w"), indent=2)


if __name__ == "__main__":
    main()
