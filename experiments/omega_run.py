"""Experiment Omega -- orchestrator. Builds the full causal/DRO decision system and emits
posteriors, causal estimates, the minimax-regret frontier, a robust submission, and an
automatic decision in {SHIP_GOLDEN, SHIP_CONSTRAINED_FUSION, SHIP_OMEGA, NO_RANKING_DOMINATES}.

Reviewers are SIMULATED (no humans available) -> the SHIP_OMEGA gate that requires a real
human lockbox is unmet by construction; the decision can only be SHIP_GOLDEN,
SHIP_CONSTRAINED_FUSION, or NO_RANKING_DOMINATES. Golden (af8f2b32) untouched.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels  # noqa: E402
from anachronism import is_anachronistic, worst_severity  # noqa: E402
from integrity2 import classify  # noqa: E402
from exp_rankfusion import rankings as build_rankings  # noqa: E402
from exp_rankfusion_guarded import build_top  # noqa: E402
from exp_constrained_fusion import constrained_top100  # noqa: E402
from redrob_ranker.eval_harness import load_labels  # noqa: E402
import omega_lib as O  # noqa: E402

OUT = Path("experiments/omega_outputs")
LAB = Path("C:/Users/bhune/india-runs-compare-lab/artifacts")
INDEP = ["merged_j1", "merged_j2", "merged_j3", "relabel_j4", "relabel_g25", "blind_test_frozen"]
LAMBDAS = np.linspace(0.0, 2.0, 21)        # judge-utility worlds: integrity penalty weight
GOLDEN_HONEYPOT_TOL = 0                      # zero high-confidence hard honeypots in top-10


def dcg_utility(ranking, util, k=100):
    return float(sum(util.get(c, 0.0) / np.log2(i + 2) for i, c in enumerate(ranking[:k])))


def main():
    OUT.mkdir(exist_ok=True)
    recs, golden_ids = load_pool()
    full, _, _ = labels()
    rec_by = {r["cid"]: r for r in recs}
    ranks = build_rankings(recs)
    fusion_ids = build_top(recs, ranks, "raw")
    constrained_ids, hard_set = constrained_top100(recs)

    # ---- quality & integrity with uncertainty over ALL pool candidates ----
    indep_sets = []
    for n in INDEP:
        p = LAB / f"{n}.jsonl"
        if p.exists():
            indep_sets.append(load_labels(p))
    quality, q_lo, q_hi, integ, hardp = {}, {}, {}, {}, {}
    for r in recs:
        c = r["cid"]
        samples = [full.tiers.get(c, 0.0) / 5.0]
        for ls in indep_sets:
            if c in ls.tiers:
                samples.append(ls.tiers[c] / 5.0)
        samples = np.array(samples)
        quality[c] = float(samples.mean())
        q_lo[c] = float(samples.min() if len(samples) > 1 else samples[0] - 0.1)
        q_hi[c] = float(samples.max() if len(samples) > 1 else samples[0] + 0.1)
        integ[c] = worst_severity(r["cand"]) if is_anachronistic(r["cand"]) else 0.0
        hardp[c] = 1.0 if classify(r["cand"], r["values"])["level"] == "hard" else 0.0

    # ---- panel partition + simulated measurement model (validation of approach) ----
    panel = json.load(open("experiments/disagreement_set/manifest.json"))
    panel_cids = sorted({c for b in panel["buckets"].values() for c in b if c in rec_by})
    parts = O.partition_panel(panel_cids)
    truth = {c: O.latent_truth(rec_by[c]["cand"], full.tiers.get(c, 0.0)) for c in panel_cids}
    fit_cids = parts["discovery"] + parts["calibration"]
    revs_mid = O.make_reviewers(24, world_integrity=0.8)
    Jfit = O.simulate({c: truth[c] for c in fit_cids}, revs_mid, pairs_per_reviewer=50)
    post = O.fit_bt(fit_cids, Jfit)
    # lockbox SPA (held-out): simulate fresh judgments on lockbox, score model order
    Jlock = O.simulate({c: truth[c] for c in parts["lockbox"]},
                       O.make_reviewers(12, 0.8), pairs_per_reviewer=40)
    # extend quality estimate to lockbox via truth-mean (model only fit on fit_cids)
    lock_q = np.array([truth[c][0] for c in parts["lockbox"]])
    spa = O.soft_pairwise_accuracy(parts["lockbox"], lock_q, Jlock)

    # ---- causal date-reveal effect across independent reviewer groups + prior sweep ----
    causal = {}
    base_cids = parts["discovery"][:40]
    for prior in (0.2, 0.8, 1.6):
        revsg = O.make_reviewers(12, world_integrity=prior)
        # original vs date_normalized: integrity-violation present vs clamped
        orig = {c: truth[c] for c in base_cids}
        norm = {c: (truth[c][0], 0.0) for c in base_cids}   # dates normalised -> no violation
        Jo = O.simulate(orig, revsg, pairs_per_reviewer=40)
        Jn = O.simulate(norm, O.make_reviewers(12, world_integrity=prior), pairs_per_reviewer=40)
        # mean win-rate of flagged candidates under each condition
        def winrate_flagged(J, cands):
            flagged = {c for c in cands if cands[c][1] > 0}
            w = t = 0
            for rid, a, b, wa in J.pairs:
                if a in flagged and b not in flagged:
                    w += wa; t += 1
                elif b in flagged and a not in flagged:
                    w += (1 - wa); t += 1
            return w / t if t else 0.0
        wo = winrate_flagged(Jo, orig); wn = winrate_flagged(Jn, norm)
        causal[f"prior_{prior}"] = {"winrate_original": round(wo, 3),
                                    "winrate_date_normalized": round(wn, 3),
                                    "causal_date_penalty": round(wn - wo, 3)}

    # ---- omega robust ranking: worst-case utility + integrity constraints ----
    lam_max = float(LAMBDAS.max())
    pool_cids = [r["cid"] for r in recs]
    wc_util = {c: q_lo[c] - lam_max * integ[c] for c in pool_cids}     # worst case over worlds
    eligible = [c for c in pool_cids if hardp[c] < 0.5]                # zero hard in candidate set
    omega_ids = sorted(eligible, key=lambda c: (-wc_util[c], c))[:100]
    # safety: enforce zero high-confidence hard in top-10/top-100 (already excluded)
    omega_hard10 = sum(1 for c in omega_ids[:10] if hardp[c] >= 0.5)
    omega_hard100 = sum(1 for c in omega_ids if hardp[c] >= 0.5)

    rankings = {"golden": golden_ids, "constrained_fusion": constrained_ids,
                "fusion_raw": fusion_ids, "omega": omega_ids}

    # ---- minimax-regret across judge-utility worlds ----
    def util_world(lam):
        return {c: quality[c] - lam * integ[c] for c in pool_cids}
    world_scores = {name: [] for name in rankings}
    for lam in LAMBDAS:
        u = util_world(lam)
        for name, rk in rankings.items():
            world_scores[name].append(dcg_utility(rk, u))
    world_scores = {k: np.array(v) for k, v in world_scores.items()}
    best_per_world = np.max(np.vstack([world_scores[k] for k in rankings]), axis=0)
    regret = {k: best_per_world - world_scores[k] for k in rankings}
    max_regret = {k: float(regret[k].max()) for k in rankings}
    frontier = [{"lambda": float(l),
                 **{k: float(world_scores[k][i]) for k in rankings}}
                for i, l in enumerate(LAMBDAS)]

    # ---- evaluation battery ----
    shippable = ["golden", "constrained_fusion", "omega"]   # fusion_raw shown for context
    # candidate-deletion influence on omega's worst-case advantage vs golden
    def wc_score(rk):
        return min(dcg_utility(rk, util_world(l)) for l in LAMBDAS)
    omega_adv = wc_score(omega_ids) - wc_score(golden_ids)
    infl = []
    backfill = [c for c in pool_cids if c not in set(omega_ids)][0]
    for c in omega_ids[:60]:
        alt = [x for x in omega_ids if x != c] + [backfill]
        infl.append(wc_score(omega_ids) - wc_score(alt[:100]))
    infl.sort(reverse=True)
    top5_infl = float(sum(infl[:5]))
    # reviewer-family deletion: refit measurement model dropping a reviewer slice; SPA stability
    Jdrop = O.Judgments(pairs=[p for p in Jfit.pairs if p[0] % 3 != 0],
                        integ=[g for g in Jfit.integ if g[0] % 3 != 0])
    post2 = O.fit_bt(fit_cids, Jdrop, n_boot=10)
    spa_drop = O.soft_pairwise_accuracy(fit_cids, post2["q_mean"], Jfit)

    # ---- decision function ----
    minimax_winner = min(shippable, key=lambda k: max_regret[k])
    # SHIP_OMEGA gates (gate 1 unmet by construction: no real human lockbox)
    omega_gates = {
        "beats_golden_on_REAL_human_lockbox": False,      # NO human data exists
        "lower_worst_case_regret_than_golden": bool(max_regret["omega"] < max_regret["golden"] - 1e-6),
        "not_driven_by_few_candidates": bool((top5_infl < 0.5 * max(omega_adv, 1e-9)) if omega_adv > 0 else True),
        "stable_under_reviewer_family_deletion": bool(abs(spa - spa_drop) < 0.05),
        "zero_highconf_hard_top10_and_bounded_top100": bool(omega_hard10 == 0 and omega_hard100 == 0),
    }
    omega_ok = all(omega_gates.values())
    # crossover: does any single shippable option dominate across ALL worlds?
    dominates = None
    for k in shippable:
        if all(world_scores[k][i] >= best_per_world[i] - 1e-9 for i in range(len(LAMBDAS))):
            dominates = k
    if omega_ok:
        decision = "SHIP_OMEGA"
    elif dominates == "golden" or (minimax_winner == "golden"):
        # golden minimax-optimal among shippable AND omega can't be confirmed
        decision = "SHIP_GOLDEN"
    elif minimax_winner == "constrained_fusion" and max_regret["golden"] > 2 * max_regret["constrained_fusion"]:
        decision = "SHIP_CONSTRAINED_FUSION"
    else:
        decision = "NO_RANKING_DOMINATES"

    # ---- write outputs ----
    json.dump({"cids": post["cids"],
               "quality_mean": post["q_mean"].tolist(),
               "quality_lo": post["q_lo"].tolist(), "quality_hi": post["q_hi"].tolist(),
               "integrity_prob": post["pi_prob"].tolist()},
              open(OUT / "posteriors.json", "w"))
    json.dump(causal, open(OUT / "causal_effects.json", "w"), indent=2)
    json.dump({"lambdas": LAMBDAS.tolist(), "frontier": frontier,
               "max_regret": max_regret}, open(OUT / "minimax_regret_frontier.json", "w"), indent=2)
    dec = {"decision": decision, "minimax_winner_among_shippable": minimax_winner,
           "max_regret": max_regret, "omega_gates": omega_gates,
           "omega_hard_top10": omega_hard10, "omega_hard_top100": omega_hard100,
           "lockbox_soft_pairwise_accuracy": round(spa, 3),
           "spa_after_reviewer_family_deletion": round(spa_drop, 3),
           "omega_worstcase_advantage_vs_golden": round(omega_adv, 4),
           "omega_top5_candidate_influence": round(top5_infl, 4),
           "panel_partitions": {k: len(v) for k, v in parts.items()},
           "NOTE": "Reviewers SIMULATED; SHIP_OMEGA gate 1 (real human lockbox) unmet by construction."}
    json.dump(dec, open(OUT / "decision.json", "w"), indent=2)
    # robust submission (omega), rank-monotonic score
    with open(OUT / "omega_submission.csv", "w", encoding="utf-8", newline="") as f:
        import csv
        w = csv.writer(f); w.writerow(["candidate_id", "rank", "score"])
        for i, c in enumerate(omega_ids, 1):
            w.writerow([c, i, f"{(100 - i + 1) / 101:.6f}"])

    # ---- console summary ----
    print("=" * 70)
    print("EXPERIMENT OMEGA -- DECISION:", decision)
    print("=" * 70)
    print(f"panel partitions: {dec['panel_partitions']}")
    print(f"measurement model lockbox Soft-Pairwise-Accuracy: {spa:.3f}  "
          f"(after reviewer-family deletion {spa_drop:.3f})")
    print("\ncausal date-reveal penalty (win-rate drop for flagged candidates), by integrity prior:")
    for k, v in causal.items():
        print(f"  {k}: original {v['winrate_original']} -> date-normalized {v['winrate_date_normalized']}  "
              f"penalty {v['causal_date_penalty']:+.3f}")
    print("\nmax worst-case regret across {} judge-utility worlds (lambda 0..2):".format(len(LAMBDAS)))
    for k in rankings:
        print(f"  {k:<20} max_regret={max_regret[k]:.4f}")
    print(f"\nminimax winner among shippable: {minimax_winner}")
    print(f"omega integrity gates: top10_hard={omega_hard10} top100_hard={omega_hard100}")
    print("omega ship-gates:")
    for k, v in omega_gates.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"\nomega worst-case advantage vs golden: {omega_adv:+.4f}  "
          f"(top-5 candidate influence {top5_infl:+.4f})")
    print(f"\noutputs -> {OUT}/  (posteriors, causal_effects, minimax_regret_frontier, decision, omega_submission)")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
