#!/usr/bin/env python3
"""Hedge simulation (read-only study; submission.csv is NOT modified).

Question (2026-06-11 adversarial audit, kill-list #1): the shipped ranking
behaviorally demotes 11 gold-stratum "perfect-on-paper but unavailable"
profiles out of the top-100. That is correct if the hidden labels encode
availability (the JD says to down-weight the unavailable) and costly if they
do not. This study measures — against all committed label sources — what two
hedged orderings would have scored:

  variant TAIL: shipped top-90 + the demoted non-honeypot gold profiles
                inserted at ranks 91-100 (current ranks 91-100 displaced).
                Touches only MAP among the composite terms.
  variant MID:  same profiles inserted at ranks 41-50 (current 41-90 shift
                down; 91-100 displaced). Also moves NDCG@50 — the aggressive
                version, shown for completeness.

Gold strata are recovered from artifacts/forensics_features.jsonl (the two
top summary templates, docs/generator_forensics.md). Any profile with a hard
honeypot flag (artifacts/honeypot_flagged.jsonl) is excluded from insertion —
a hedge must never add a honeypot to the top-100.

All scoring goes through the shared harness (challenge composite,
policy=exclude, coverage reported). Output: stdout table for
docs/hedge_simulation_study.md.

Because 9 of the 10 demoted golds carry no judge label (they never entered any
judged sample), the committed proxies cannot adjudicate the hedge directly. So
this study also builds an AVAILABILITY-BLIND variant of the independent
labeler (the H2 label hypothesis made concrete): every candidate's
reachability signals are normalized to the same "reachable" values before
labeling, so the availability term becomes a constant and labels reflect fit
only. Fit, seniority, honeypot, and JD-disqualifier logic are untouched.
Cached at artifacts/h2_availblind_labels.jsonl.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.eval_harness import (  # noqa: E402
    evaluate,
    load_labels,
    load_submission,
)

GOLD_TEMPLATES = {
    "senior ai engineer with # years",
    "senior engineer who has spent the",
}

LABEL_SOURCES = [
    (ROOT / "artifacts" / "independent_labels_100k.jsonl", "independent"),
    (ROOT / "docs" / "llm_judge_eval_labels.jsonl", "judge1"),
    (ROOT / "docs" / "llm_judge_eval_2_labels.jsonl", "judge2"),
]


def build_h2_labels(path: Path) -> None:
    """Label all 100K with the independent labeler, availability-neutralized."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_independent_labels import label_candidate  # noqa: E402

    with open(ROOT / "candidates.jsonl", encoding="utf-8") as src, \
            open(path, "w", encoding="utf-8") as out:
        for line in src:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            sig = dict(c.get("redrob_signals") or {})
            # Constant "reachable" signals for everyone -> the availability
            # term cancels; only fit/seniority/disqualifiers differentiate.
            sig["recruiter_response_rate"] = 0.6
            sig["open_to_work_flag"] = True
            sig["last_active_date"] = "2026-06-01"
            c["redrob_signals"] = sig
            tier, relevance, reasons = label_candidate(c)
            out.write(json.dumps({
                "candidate_id": c["candidate_id"], "tier": tier,
                "relevance": round(relevance, 4), "reasons": reasons,
            }) + "\n")


def load_gold_ids() -> list[str]:
    ids = []
    with open(ROOT / "artifacts" / "forensics_features.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("summary_template") in GOLD_TEMPLATES:
                ids.append(rec["candidate_id"])
    return ids


def load_honeypot_ids() -> set[str]:
    ids = set()
    with open(ROOT / "artifacts" / "honeypot_flagged.jsonl", encoding="utf-8") as fh:
        for line in fh:
            ids.add(json.loads(line)["candidate_id"])
    return ids


def score_all(name: str, ranked: list[str], sets) -> dict[str, float]:
    print(f"\n{name} (n={len(ranked)}):")
    composites = {}
    for ls in sets:
        r = evaluate(ranked, ls, unlabeled="exclude")
        composites[ls.name] = r.composite
        print(
            f"  {ls.name:<12} NDCG@10={r.ndcg10:.4f} NDCG@50={r.ndcg50:.4f} "
            f"MAP={r.map:.4f} P@10={r.p10:.4f} composite={r.composite:.4f} "
            f"coverage={r.coverage:.1%}"
        )
    gate = [v for k, v in composites.items() if k != "H2-availblind"]
    mean = sum(gate) / len(gate)
    print(f"  {'MEAN(gate3)':<12} composite={mean:.4f}  "
          f"(H2-availblind reported separately, not part of the gate mean)")
    composites["mean"] = mean
    return composites


def main() -> None:
    shipped = load_submission(ROOT / "submission.csv")
    top100 = set(shipped)
    gold = load_gold_ids()
    honeypots = load_honeypot_ids()
    h2_path = ROOT / "artifacts" / "h2_availblind_labels.jsonl"
    if not h2_path.exists():
        print("building availability-blind (H2) labels for all 100K ...")
        build_h2_labels(h2_path)
    sets = [load_labels(p, name) for p, name in LABEL_SOURCES]
    sets.append(load_labels(h2_path, "H2-availblind"))
    j1, j2, ind = sets[1], sets[2], sets[0]

    in_top = [c for c in gold if c in top100]
    demoted = [c for c in gold if c not in top100]
    insert = [c for c in demoted if c not in honeypots]
    excluded_hp = [c for c in demoted if c in honeypots]
    print(f"gold-strata profiles: {len(gold)} "
          f"(in top-100: {len(in_top)}, demoted: {len(demoted)}, "
          f"honeypot-excluded from hedge: {excluded_hp})")

    # Deterministic insertion order: judge1 tier desc, judge2 tier desc,
    # independent relevance desc, candidate_id asc.
    insert.sort(key=lambda c: (
        -j1.tiers.get(c, -1.0),
        -j2.tiers.get(c, -1.0),
        -ind.gains.get(c, -1.0),
        c,
    ))
    print("inserted (rank order):")
    for c in insert:
        print(f"  {c}  j1={j1.tiers.get(c, '-')} j2={j2.tiers.get(c, '-')} "
              f"ind={ind.gains.get(c, '-')}")

    k = len(insert)
    tail = shipped[: 100 - k] + insert
    mid = shipped[:40] + insert + shipped[40 : 100 - k]
    displaced = shipped[100 - k :]
    print(f"\ndisplaced from ranks {100 - k + 1}-100: {displaced}")

    base = score_all("SHIPPED", shipped, sets)
    tail_r = score_all(f"HEDGE-TAIL (insert at {100 - k + 1}-100)", tail, sets)
    mid_r = score_all("HEDGE-MID (insert at 41-50)", mid, sets)

    print("\ncomposite deltas vs shipped:")
    print(f"{'source':<12} {'tail':>9} {'mid':>9}")
    for key in [ls.name for ls in sets] + ["mean"]:
        print(f"{key:<12} {tail_r[key] - base[key]:>+9.4f} {mid_r[key] - base[key]:>+9.4f}")


if __name__ == "__main__":
    main()
