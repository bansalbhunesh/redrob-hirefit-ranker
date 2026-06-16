"""Decisive paired evaluation: rrf-lock30 vs hedge on the candidates that differ, using the blinded
integrity-aware judge tiers. Reports paired delta + bootstrap CI, majority wins, clean-candidate
performance, top-rank regressions, and results INCLUDING and EXCLUDING integrity-flagged candidates.
Decision rule: ship rrf-lock30 only if its promoted candidates stay clearly superior AFTER integrity
adjustment; else ship the hedge."""
import json, sys
from pathlib import Path
import numpy as np

DIFF = Path("experiments/diff_rrf_vs_hedge.json")
JUDGE = Path("experiments/fresh_judge_decisive.jsonl")
rng = np.random.default_rng(0)


def boot_ci(x, n=10000):
    x = np.asarray(x, float)
    if len(x) == 0:
        return (0.0, 0.0)
    m = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
    return (round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3))


def summary(deltas, label):
    a = np.array(deltas, float)
    if len(a) == 0:
        print(f"  {label:<34} (no pairs)"); return
    lo, hi = boot_ci(a)
    rw = int((a > 0).sum()); hw = int((a < 0).sum()); tie = int((a == 0).sum())
    print(f"  {label:<34} n={len(a):>2}  mean d={a.mean():+.3f} 95%CI[{lo:+.3f},{hi:+.3f}]  "
          f"rrf>hedge {rw} / hedge>rrf {hw} / tie {tie}")
    return a.mean(), lo, hi, rw, hw


def main():
    d = json.loads(DIFF.read_text())
    tier = {}; integ = {}
    for l in JUDGE.open(encoding="utf-8"):
        if l.strip():
            r = json.loads(l); tier[r["candidate_id"]] = r["tier"]; integ[r["candidate_id"]] = r["integrity"]
    pairs = d["pairs"]
    have = lambda c: c in tier
    # integrity distribution among rrf-only (what rrf newly promotes)
    from collections import Counter
    rrf_only, hedge_only = d["rrf_only"], d["hedge_only"]
    print("Integrity classification (blinded judge):")
    print("  rrf-only promotions:", dict(Counter(integ.get(c, "?") for c in rrf_only)))
    print("  hedge-only promotions:", dict(Counter(integ.get(c, "?") for c in hedge_only)))
    print()

    # paired deltas by rank (rrf tier - hedge tier)
    full, clean, excl_contra = [], [], []
    toprank_reg = []
    for p in pairs:
        rc, hc, rank = p["rrf"], p["hedge"], p["rank"]
        if not (have(rc) and have(hc)):
            continue
        delta = tier[rc] - tier[hc]
        full.append(delta)
        # clean = neither side a contradiction
        if integ.get(rc) != "contradiction" and integ.get(hc) != "contradiction":
            clean.append(delta)
        # integrity-adjusted: drop pairs where rrf's pick is a contradiction (its added risk)
        if integ.get(rc) != "contradiction":
            excl_contra.append(delta)
        if delta < 0 and rank <= 50:
            toprank_reg.append((rank, rc, hc, tier[rc], tier[hc]))

    print("Paired quality (rrf candidate tier - hedge candidate tier), per differing rank:")
    summary(full, "INCLUDING flagged (all pairs)")
    summary(excl_contra, "integrity-adjusted (drop rrf contra)")
    summary(clean, "CLEAN only (no contradiction either)")

    print(f"\nTop-rank regressions (rank<=50 where rrf candidate is WORSE): {len(toprank_reg)}")
    for rank, rc, hc, rt, ht in sorted(toprank_reg)[:8]:
        print(f"  rank {rank}: rrf {rc}(t{rt}) < hedge {hc}(t{ht})  [rrf integ={integ.get(rc)}]")

    # decision
    a = np.array(excl_contra, float)
    lo, hi = boot_ci(a) if len(a) else (0, 0)
    clearly_superior = len(a) > 0 and a.mean() > 0 and lo > 0
    print("\n" + "=" * 70)
    if clearly_superior:
        print("DECISION: rrf-lock30 promotions remain CLEARLY SUPERIOR after integrity adjustment")
        print("          (mean>0 and 95% CI excludes 0) -> SHIP rrf-lock30.")
    else:
        print("DECISION: rrf-lock30 NOT clearly superior after integrity adjustment")
        print(f"          (integrity-adjusted mean d={a.mean() if len(a) else 0:+.3f}, 95%CI[{lo:+.3f},{hi:+.3f}] includes 0 or <0)")
        print("          -> SHIP the HEDGE.")


if __name__ == "__main__":
    main()
