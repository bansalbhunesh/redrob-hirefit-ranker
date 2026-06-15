"""Diagnostic: WHERE does the rank-fusion gain come from? A proxy gain is only real
if it promotes clean, genuinely-stronger candidates -- not honeypots / JD-disqualified
profiles that inflate the blind proxy but would be caught by human judges.

For the modal nested-selected config (RRF all eq K=30 lock20) we report:
  - per-metric delta (is the gain in NDCG@50, the documented weak spot?)
  - the candidates fusion ADDS vs golden top-100: their hand-rank, blind tier/gain,
    and integrity flags (anachronism / disqualifier / honeypot)
  - the golden candidates fusion DROPS: their tier/gain
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels  # noqa: E402
from exp_rankfusion import FAMILIES, rankings, rrf_scores, fuse_topk  # noqa: E402
from redrob_ranker.eval_harness import evaluate  # noqa: E402

try:
    from anachronism import is_anachronistic, worst_severity
except Exception:
    is_anachronistic = None


def main():
    recs, base_ids = load_pool()
    full, _, _ = labels()
    ranks = rankings(recs)
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    rec_by = {r["cid"]: r for r in recs}
    hand_rank = {c: i + 1 for i, c in enumerate(
        sorted(cids, key=lambda c: (-rec_by[c]["hand"], c)))}

    eq = {f: 1.0 for f in FAMILIES}
    fused = rrf_scores(cids, ranks, list(FAMILIES), eq, 30)
    top = fuse_topk(recs, fused, hand, 20)

    b = evaluate(base_ids, full)
    f = evaluate(top, full)
    print("config: RRF all-families equal, K=30, top-lock=20")
    print(f"{'metric':<12}{'golden':>9}{'fusion':>9}{'delta':>9}")
    for m in ("ndcg10", "ndcg50", "map", "p10", "composite"):
        gv, fv = getattr(b, m), getattr(f, m)
        print(f"{m:<12}{gv:>9.4f}{fv:>9.4f}{fv - gv:>+9.4f}")

    added = [c for c in top if c not in set(base_ids)]
    dropped = [c for c in base_ids if c not in set(top)]
    print(f"\nfusion changes {len(added)} of 100 slots vs golden\n")

    def flags_of(c):
        r = rec_by.get(c, {})
        fl = set(r.get("flags") or [])
        tags = []
        if is_anachronistic and r.get("cand") and is_anachronistic(r["cand"]):
            tags.append(f"ANACHRON({worst_severity(r['cand'])})")
        if any("disq" in str(x).lower() for x in fl):
            tags.append("DISQ")
        if any("honeypot" in str(x).lower() or "trap" in str(x).lower() for x in fl):
            tags.append("HONEYPOT")
        if r.get("disq_mult", 1.0) < 1.0:
            tags.append(f"disq_mult={r['disq_mult']:.2f}")
        if r.get("honeypot_mult", 1.0) < 1.0:
            tags.append(f"hp_mult={r['honeypot_mult']:.2f}")
        return ",".join(tags) or "clean"

    print("ADDED by fusion (cid | hand_rank | blind_tier | gain | flags):")
    add_tiers = []
    for c in sorted(added, key=lambda c: hand_rank.get(c, 9999)):
        tier = full.tiers.get(c, 0.0)
        gain = full.gains.get(c, 0.0)
        add_tiers.append(tier)
        print(f"  {c}  rank#{hand_rank.get(c,'?'):>4}  tier={tier:>4.1f}  gain={gain:>7.3f}  {flags_of(c)}")

    print("\nDROPPED from golden (cid | blind_tier | gain):")
    drop_tiers = []
    for c in dropped:
        tier = full.tiers.get(c, 0.0)
        drop_tiers.append(tier)
        print(f"  {c}  tier={tier:>4.1f}  gain={full.gains.get(c,0.0):>7.3f}  {flags_of(c)}")

    n_anachron = sum(1 for c in added if is_anachronistic and rec_by.get(c, {}).get("cand")
                     and is_anachronistic(rec_by[c]["cand"]))
    print("\n--- VERDICT INPUTS ---")
    print(f"added mean blind tier:   {np.mean(add_tiers):.2f}" if add_tiers else "no additions")
    print(f"dropped mean blind tier: {np.mean(drop_tiers):.2f}" if drop_tiers else "no drops")
    print(f"anachronism-flagged among {len(added)} additions: {n_anachron}")
    deep = [c for c in added if hand_rank.get(c, 9999) > 150]
    print(f"deep-tail promotions (hand rank > 150): {len(deep)}  {deep[:10]}")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
