"""Experiment 4 — high-power repeated-holdout test of the interaction signals.
20 repeated 50/50 splits. A real effect shows mean>0 AND pos close to 20/20.
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np
sys.path.insert(0, "experiments")
from _lib import load_pool, gate_repeat


def main():
    recs, base_ids = load_pool()

    def v(r, k):
        return float(r["values"].get(k, 0.0))

    role = np.array([r["role_fit"] for r in recs])
    depth = np.array([r["ai_depth"] for r in recs])
    prod = np.array([r["production_evidence"] for r in recs])
    senior = np.array([v(r, "senior_title_held") for r in recs])

    R = 20
    res = []
    res.append(gate_repeat(recs, base_ids, prod, "production ALONE (control)", R=R))
    res.append(gate_repeat(recs, base_ids, role * prod, "role x production", R=R))
    res.append(gate_repeat(recs, base_ids, depth * prod, "ai_depth x production", R=R))
    res.append(gate_repeat(recs, base_ids, role * depth * prod, "role x depth x production", R=R))
    res.append(gate_repeat(recs, base_ids, prod * (role + depth + senior), "prod x (role+depth+senior)", R=R))

    print("\n================ VERDICT (20 repeated 50/50 holdouts) ================")
    for r in sorted(res, key=lambda x: -x["mean"]):
        stable = r["pos"] >= int(0.85 * r["R"]) and r["mean"] > 0.002
        tag = "ROBUST WIN" if stable else ("weak/noisy" if r["mean"] > 0 else "no effect")
        print(f"{r['name']:<32} mean {r['mean']:+.4f}  pos {r['pos']}/{r['R']}  [{tag}]")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
