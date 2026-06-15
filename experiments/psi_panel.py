"""Experiment Psi -- Minimal Human Integrity Calibration: PANEL CONSTRUCTION.

Builds the frozen, pre-registered instrument that estimates the ONE missing quantity Omega
exposed: how strongly REAL humans penalise a decisive integrity contradiction after seeing
strong career evidence (the unknown lambda; crossover at lambda~0.10).

This module ONLY constructs and freezes the panel + blinded two-stage packets. It collects
NO judgments (no humans available). The sampling RULE and candidate hashes are frozen here,
BEFORE any selection on the Omega posterior, so the panel is a genuine lockbox. Selection
uses only pre-Omega signals: shipped hand score, the anachronism detector, and fusion
marginal influence.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels  # noqa: E402
from anachronism import is_anachronistic, worst_severity  # noqa: E402
from exp_rankfusion import rankings as build_rankings  # noqa: E402
from exp_rankfusion_guarded import build_top  # noqa: E402
from redrob_ranker.eval_harness import evaluate  # noqa: E402
from redrob_ranker.text import candidate_text  # noqa: E402
from omega_lib import make_variants  # noqa: E402

OUT = Path("experiments/psi_panel")

SAMPLING_RULE = {
    "version": "psi-2026-06-15",
    "source": "frozen disagreement population (pool-ranked), pre-Omega signals only",
    "composition": {
        "fusion_gain_drivers (anachronism, top-5 marginal influence)": 5,
        "matched_clean (nearest hand-score clean candidate to each driver)": 5,
        "hard_integrity_controls (highest anachronism severity)": 4,
        "ambiguous_date_quality (mid anachronism severity ~1.0)": 4,
        "strong_clean (top hand, no flag)": 3,
        "weak_clean (low hand, no flag)": 3,
    },
    "blinding": "Stage A = date_hidden variant (no dates/durations, no flags shown); "
                "Stage B = full original profile. Reviewer never told selector (golden/fusion/omega).",
    "note": "Selection uses hand score + anachronism detector + fusion influence ONLY; "
            "NOT the simulated Omega posterior.",
}


def main():
    OUT.mkdir(exist_ok=True)
    recs, golden_ids = load_pool()
    full, _, _ = labels()
    rec_by = {r["cid"]: r for r in recs}
    hand = {r["cid"]: r["hand"] for r in recs}
    anach = {r["cid"]: (worst_severity(r["cand"]) if is_anachronistic(r["cand"]) else 0.0) for r in recs}

    # --- fusion gain drivers: top-5 added candidates by marginal composite influence ---
    ranks = build_rankings(recs)
    fusion = build_top(recs, ranks, "raw")
    gold = set(golden_ids)
    added = [c for c in fusion if c not in gold]
    f0 = evaluate(fusion, full).composite
    backfill = [r["cid"] for r in recs if r["cid"] not in set(fusion)][0]
    infl = []
    for c in added:
        alt = [x for x in fusion if x != c] + [backfill]
        infl.append((c, f0 - evaluate(alt[:100], full).composite))
    infl.sort(key=lambda t: -t[1])
    drivers = [c for c, _ in infl[:5]]

    clean = [c for c in (r["cid"] for r in recs) if anach[c] == 0.0]
    used = set(drivers)
    # matched clean: nearest hand score to each driver
    matched = []
    for d in drivers:
        cand = min((c for c in clean if c not in used), key=lambda c: abs(hand[c] - hand[d]))
        matched.append(cand); used.add(cand)
    # hard-integrity controls: highest anachronism severity
    hard_ctrl = [c for c in sorted(anach, key=lambda c: -anach[c]) if anach[c] > 0 and c not in used][:4]
    used.update(hard_ctrl)
    # ambiguous date-quality: anachronism severity near 1.0 (borderline)
    amb = [c for c in sorted(anach, key=lambda c: abs(anach[c] - 1.0)) if anach[c] > 0 and c not in used][:4]
    used.update(amb)
    # strong clean (top hand) / weak clean (low hand among pool clean)
    clean_sorted = sorted((c for c in clean if c not in used), key=lambda c: -hand[c])
    strong_clean = clean_sorted[:3]; used.update(strong_clean)
    weak_clean = clean_sorted[-3:]; used.update(weak_clean)

    buckets = {"fusion_gain_drivers": drivers, "matched_clean": matched,
               "hard_integrity_controls": hard_ctrl, "ambiguous_date_quality": amb,
               "strong_clean": strong_clean, "weak_clean": weak_clean}
    all_cids = [c for b in buckets.values() for c in b]
    assert len(all_cids) == len(set(all_cids)), "overlap in panel"

    frozen_hash = hashlib.sha256(
        (json.dumps(SAMPLING_RULE, sort_keys=True) + "|" + "|".join(sorted(all_cids))).encode()).hexdigest()

    # committed manifest: cids + buckets + rule + hash (NO profile text)
    json.dump({"sampling_rule": SAMPLING_RULE, "frozen_hash": frozen_hash,
               "total": len(all_cids), "buckets": buckets,
               "driver_influence": [{"cid": c, "marginal_composite": round(v, 5)} for c, v in infl[:5]]},
              open(OUT / "manifest.json", "w"), indent=2)

    # gitignored blinded two-stage reviewer packets (profiles). Shuffle; anon ids.
    import random
    rng = random.Random(0)
    rows = []
    for c in all_cids:
        v = make_variants(rec_by[c]["cand"])
        rows.append({"anon_id": hashlib.md5((c + "|psi").encode()).hexdigest()[:10],
                     "stageA_profile_no_dates": candidate_text(v["date_hidden"])[:3500],
                     "stageB_profile_full": candidate_text(v["original"])[:3500]})
    rng.shuffle(rows)
    with open(OUT / "reviewer_packet.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            # Stage A questions
            r_out = {"anon_id": r["anon_id"], "stageA_profile_no_dates": r["stageA_profile_no_dates"],
                     "A1_suitability_0to5": None, "A2_belongs_top100_yes_no": None,
                     "A3_supporting_evidence": None, "A4_confidence_low_med_high": None,
                     "stageB_profile_full": r["stageB_profile_full"],
                     "B1_decision_materially_changes_yes_no": None,
                     "B2_issue_class_[noise|incomplete|suspicious|decisive_impossibility]": None,
                     "B3_remain_top100_yes_no": None, "B4_reject_regardless_yes_no": None,
                     "B5_confidence_low_med_high": None}
            f.write(json.dumps(r_out) + "\n")
    # anon->cid+bucket key (gitignored) for scoring after responses return
    json.dump({hashlib.md5((c + "|psi").encode()).hexdigest()[:10]:
               {"cid": c, "bucket": next(b for b, ids in buckets.items() if c in ids)}
               for c in all_cids}, open(OUT / "anon_key.json", "w"))

    print(f"Psi panel frozen: {len(all_cids)} candidates, hash {frozen_hash[:16]}")
    for b, ids in buckets.items():
        print(f"  {b:<26} {len(ids)}")
    print("driver marginal influence:", [(c, round(v, 4)) for c, v in infl[:5]])
    print(f"manifest -> {OUT/'manifest.json'} (committed); reviewer_packet.jsonl + anon_key.json (gitignored)")
    print("\nNO judgments collected -- awaiting 9 real reviewers (3 recruiters / 3 engineers / 3 neutral).")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
