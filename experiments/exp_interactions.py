"""Experiment 1 — interaction features (beat-the-linear-model ideas).

A weighted-sum scorer cannot represent feature interactions. Competitors encode them:
a ×1.12 synergy bonus (on-target title AND real retrieval evidence);
multiplicative funnels. We test products of our own
features as added signal, holdout-gated.
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np
sys.path.insert(0, "experiments")
from _lib import load_pool, gate


def main():
    recs, base_ids = load_pool()

    def v(r, k):
        return float(r["values"].get(k, 0.0))

    role = np.array([r["role_fit"] for r in recs])
    depth = np.array([r["ai_depth"] for r in recs])
    prod = np.array([r["production_evidence"] for r in recs])
    prodco = np.array([v(r, "product_company_ratio") for r in recs])
    senior = np.array([v(r, "senior_title_held") for r in recs])
    traj = np.array([v(r, "career_trajectory_score") for r in recs])

    results = []
    results.append(gate(recs, base_ids, role * prod, "role_fit x production"))
    results.append(gate(recs, base_ids, depth * prod, "ai_depth x production"))
    results.append(gate(recs, base_ids, senior * prod, "senior_title x production"))
    results.append(gate(recs, base_ids, prodco * depth, "product_company x ai_depth"))
    results.append(gate(recs, base_ids, role * depth * prod, "role x depth x production (triple)"))
    results.append(gate(recs, base_ids, traj * prod, "trajectory x production"))

    # an external baseline-style synergy bonus as a multiplicative factor
    bonus = 1.0 + 0.12 * ((role > 0.6) & (prod > 0.5)).astype(float)
    results.append(gate(recs, base_ids, bonus, "synergy_bonus 1.12 (title&evidence)", mode="mult", weights=[0.0, 1.0, 2.0, 3.0]))

    print("\n================ SUMMARY (interactions) ================")
    for r in sorted(results, key=lambda x: -x["holdout_delta"]):
        print(f"{r['name']:<40} holdout {r['holdout_delta']:+.4f}  best_full {r['best_full']:.4f}  [{r['verdict']}]")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
