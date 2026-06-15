"""Freeze a PROSPECTIVE disagreement set (lockbox) for integrity-aware human review.

This is the experiment that actually resolves golden-vs-fusion (A vs B): a human panel
answers two SEPARATE blind questions per candidate -- (1) job fit for the Senior AI
Engineer JD, (2) does the profile contain a DECISIVE impossible contradiction -- WITHOUT
seeing rank, selector, detector flag, or any model label. A candidate can be tier-5 on
fit yet tier-0 under the hackathon if it is a planted honeypot.

We freeze the fusion parameters and the candidate selection BEFORE any labels exist
(recorded hash), so the set is a genuine lockbox, not another tuning set. Output:
  - disagreement_set/manifest.json   (committed: ids + buckets + frozen-params hash; no PII)
  - disagreement_set/reviewer_packet.jsonl (gitignored: shuffled profiles + blank Q1/Q2)
"""
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")

from _lib import load_pool  # noqa: E402
from integrity2 import classify  # noqa: E402
from exp_rankfusion import rankings as build_rankings  # noqa: E402
from exp_rankfusion_guarded import build_top  # noqa: E402
from redrob_ranker.text import candidate_text  # noqa: E402

OUTDIR = Path("experiments/disagreement_set")
FROZEN_PARAMS = {"fusion": "RRF K=30 top-lock=10, 5 complementary channels",
                 "detector": "integrity2 (hard=anachronism+timeline+edu+multi-current+expert0-uncorrob)",
                 "selector_version": "2026-06-15"}
CAP = 220


def main():
    recs, base_ids = load_pool()
    rec_by = {r["cid"]: r for r in recs}
    hand_rank = {r["cid"]: i + 1 for i, r in enumerate(
        sorted(recs, key=lambda r: (-r["hand"], r["cid"])))}
    ranks = build_rankings(recs)
    fusion = set(build_top(recs, ranks, "raw"))
    golden = set(base_ids)
    hard = {r["cid"] for r in recs if classify(r["cand"], r["values"])["level"] == "hard"}

    buckets = {}
    # 1. golden vs fusion disagreements
    buckets["golden_only"] = sorted(golden - fusion)[:40]
    buckets["fusion_only"] = sorted(fusion - golden)[:40]
    # 2. flagged candidates fusion promotes
    buckets["flagged_promoted"] = sorted(hard & fusion)[:40]
    # 3. flagged candidates fusion does NOT promote
    buckets["flagged_not_promoted"] = sorted(hard - fusion)[:30]
    # 4. clean candidates of similar (high) career quality
    clean_top = [r["cid"] for r in sorted(recs, key=lambda r: (-r["hand"], r["cid"]))
                 if r["cid"] not in hard][:300]
    buckets["clean_high_quality"] = [c for c in clean_top if c not in golden and c not in fusion][:30]
    # 5. boundary rank bands 8-20 and 40-70
    bands = [r["cid"] for r in recs if hand_rank[r["cid"]] in range(8, 21) or hand_rank[r["cid"]] in range(40, 71)]
    buckets["rank_boundary"] = sorted(bands)[:40]

    # dedup preserving bucket membership; cap total
    seen, manifest_buckets = set(), {}
    for b, ids in buckets.items():
        keep = [c for c in ids if c not in seen]
        for c in keep:
            seen.add(c)
        manifest_buckets[b] = keep
    all_ids = sorted(seen)[:CAP]

    frozen_hash = hashlib.sha256(
        (json.dumps(FROZEN_PARAMS, sort_keys=True) + "|" + "|".join(all_ids)).encode()).hexdigest()

    OUTDIR.mkdir(exist_ok=True)
    json.dump({"frozen_params": FROZEN_PARAMS, "frozen_hash": frozen_hash,
               "total": len(all_ids), "buckets": manifest_buckets},
              open(OUTDIR / "manifest.json", "w"), indent=2)

    # gitignored reviewer packet: shuffled, blind (no rank/flag/selector)
    packet = []
    for c in all_ids:
        packet.append({"anon_id": hashlib.md5(c.encode()).hexdigest()[:10],
                       "profile": candidate_text(rec_by[c]["cand"])[:4000],
                       "q1_job_fit_0to5": None,
                       "q2_decisive_impossible_contradiction_yes_no": None})
    random.Random(0).shuffle(packet)
    with open(OUTDIR / "reviewer_packet.jsonl", "w", encoding="utf-8") as f:
        for row in packet:
            f.write(json.dumps(row) + "\n")
    # key file maps anon_id -> cid + bucket (gitignored; for scoring after labels return)
    json.dump({hashlib.md5(c.encode()).hexdigest()[:10]: {"cid": c,
               "buckets": [b for b, ids in manifest_buckets.items() if c in ids]} for c in all_ids},
              open(OUTDIR / "anon_key.json", "w"))

    print(f"frozen disagreement set: {len(all_ids)} candidates, hash {frozen_hash[:16]}")
    for b, ids in manifest_buckets.items():
        print(f"  {b:<22} {len(ids)}")
    print(f"manifest -> {OUTDIR/'manifest.json'} (committed)")
    print(f"reviewer packet -> {OUTDIR/'reviewer_packet.jsonl'} (gitignored, {len(packet)} rows, blind)")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
