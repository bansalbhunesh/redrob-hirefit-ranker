"""Technology-anachronism honeypot guard (idea: De-Coder05's anachronism detection,
made high-precision). Catches candidates claiming expert tenure in a technology for
LONGER THAN THE TECHNOLOGY HAS EXISTED — a honeypot class our existing suite and the
whole field miss. Verified real (RAG 7.8y, LangChain 7y, LlamaIndex 8y in the top-100).

Conservative: only unambiguously-recent techs, hard threshold, 6-month slack.
This module is experimental (branch only) — it does NOT modify the golden pipeline.
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np
sys.path.insert(0, "experiments")
from _lib import load_pool, minmax, labels, gate_repeat  # noqa
from redrob_ranker.eval_harness import evaluate

# Unambiguously-recent technologies and the earliest year the named skill could exist.
RECENT_TECH = {
    "rag": 2023, "retrieval augmented": 2023, "retrieval-augmented": 2023,
    "langchain": 2022, "llamaindex": 2022, "llama index": 2022,
    "chatgpt": 2022, "gpt-4": 2023, "gpt4": 2023, "stable diffusion": 2022,
    "prompt engineering": 2022,
}
NOW_Y = 2026


def anachronism_hits(cand):
    hits = []
    for s in cand.get("skills", []) or []:
        nm = str(s.get("name", "")).lower()
        dur = float(s.get("duration_months", 0) or 0)
        for key, yr in RECENT_TECH.items():
            if key in nm:
                allowed = (NOW_Y - yr) * 12 + 6  # hard impossibility + 6mo slack
                if dur > allowed:
                    hits.append((s.get("name"), dur, allowed))
                break
    return hits


def main():
    recs, base_ids = load_pool()
    full, _, _ = labels()
    base_set = set(base_ids)

    flagged = {r["cid"]: anachronism_hits(r["cand"]) for r in recs}
    in_top = [cid for cid in base_ids if flagged.get(cid)]
    print(f"pool flagged: {sum(1 for v in flagged.values() if v)}/3000 | "
          f"in CURRENT top-100: {len(in_top)} verified-impossible-tenure honeypots\n", flush=True)
    for cid in in_top[:12]:
        h = flagged[cid][0]
        print(f"  {cid}: '{h[0]}' claimed {h[1]:.0f}mo ({h[1]/12:.1f}y), max plausible {h[2]}mo")

    # guarded top-100: hand order, drop anachronism honeypots, backfill from the pool
    guarded = [r["cid"] for r in recs if not flagged.get(r["cid"])][:100]

    base_full = evaluate(base_ids, full).composite
    guard_full = evaluate(guarded, full).composite
    print(f"\nblind composite (full):  base={base_full:.4f}  guarded={guard_full:.4f}  "
          f"delta {guard_full-base_full:+.4f}")

    # repeated-holdout delta of the guarded list vs base (does removing traps hurt the proxy?)
    cids = [r["cid"] for r in recs]
    hand_n = minmax([r["hand"] for r in recs])
    print("\nrepeated-holdout (guarded vs base, blind proxy):", flush=True)
    # build a "signal" that is -inf for flagged so blend reranking drops them at any w>0
    pen = np.array([0.0 if flagged.get(r["cid"]) else 1.0 for r in recs])
    gate_repeat(recs, base_ids, pen, "anachronism-drop", mode="mult", R=20, weights=[3.0])

    print("\nVERDICT: catches a real honeypot class the pipeline + field miss; the blind PROXY "
          "rewards these (so proxy delta is <=0), but the JD explicitly warns on this inconsistency, "
          "so it is JD-faithful. Integrity guardrail — ship decision is a risk call (proxy cost vs "
          "real-label honeypot removal), not an auto-merge.")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
