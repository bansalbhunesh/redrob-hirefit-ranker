"""Experiment 2 — 5-fold CV robustness of the interaction signals + controls.
Control question: is the gain the INTERACTION, or just weighting production-evidence more?
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np
sys.path.insert(0, "experiments")
from _lib import load_pool, gate_cv


def main():
    recs, base_ids = load_pool()

    def v(r, k):
        return float(r["values"].get(k, 0.0))

    role = np.array([r["role_fit"] for r in recs])
    depth = np.array([r["ai_depth"] for r in recs])
    prod = np.array([r["production_evidence"] for r in recs])
    senior = np.array([v(r, "senior_title_held") for r in recs])
    irrank = np.array([v(r, "ir_ranking_experience") for r in recs])
    scale = np.array([v(r, "scale_signal") for r in recs])

    res = []
    print("--- controls (single features, blended) ---")
    res.append(gate_cv(recs, base_ids, prod, "production_evidence ALONE"))
    res.append(gate_cv(recs, base_ids, role, "role_fit ALONE"))
    res.append(gate_cv(recs, base_ids, depth, "ai_depth ALONE"))
    res.append(gate_cv(recs, base_ids, senior, "senior_title ALONE"))
    res.append(gate_cv(recs, base_ids, irrank, "ir_ranking_experience ALONE"))
    print("\n--- interactions ---")
    res.append(gate_cv(recs, base_ids, role * prod, "role x production"))
    res.append(gate_cv(recs, base_ids, depth * prod, "ai_depth x production"))
    res.append(gate_cv(recs, base_ids, senior * prod, "senior_title x production"))
    res.append(gate_cv(recs, base_ids, role * depth * prod, "role x depth x production"))
    res.append(gate_cv(recs, base_ids, irrank * prod, "ir_ranking x production"))
    res.append(gate_cv(recs, base_ids, prod * (role + depth + senior), "prod x (role+depth+senior)"))
    res.append(gate_cv(recs, base_ids, prod * (irrank + scale), "prod x (ir_ranking+scale)"))

    print("\n================ CV SUMMARY (sorted by mean) ================")
    for r in sorted(res, key=lambda x: -x["mean"]):
        print(f"{r['name']:<34} mean {r['mean']:+.4f}  min {r['min']:+.4f}  [{r['robust']}]")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
