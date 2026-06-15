"""Label-model sensitivity: who wins under a JD-FAITHFUL label model?

The 100K blind proxy REWARDS impossible-tenure anachronism honeypots (a tier-5 RAG
claim of 7.8y scores like any other tier-5). But the JD instructs human reviewers to
penalize inconsistent / impossible claims. So the proxy and the human-judged final
stage are misaligned exactly on the honeypot axis.

We sweep an anachronism penalty p in [0,1] applied to the blind labels (anachronism
candidates' tier and gain scaled by (1-p); p=1 == 'a human judge fully disqualifies
the impossible claim', which is what the JD says to do) and re-score four rankings:

  golden        - the shipped submission
  fusion-raw    - proxy-optimal rank fusion (promotes 25 honeypots)
  fusion-guard  - fusion with existing honeypot/disq multipliers re-applied
  fusion-clean  - rank fusion that refuses to promote anachronism candidates

p=0 reproduces the raw proxy (fusion-raw should win). The question: at what human
anachronism-aversion does golden overtake the proxy-chaser, and does fusion-clean --
a NOVEL ranking that reorders the tail WITHOUT honeypots -- become the overall best
under a human-faithful label model? That would be an evidence-backed improvement on
the axis that actually decides the prize.
"""
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from _lib import load_pool, labels  # noqa: E402
from exp_rankfusion import FAMILIES, rankings  # noqa: E402
from exp_rankfusion_guarded import build_top  # noqa: E402
from redrob_ranker.eval_harness import LabelSet, evaluate  # noqa: E402
from anachronism import is_anachronistic  # noqa: E402


def penalized_labels(full, anach_cids, p):
    tiers = {c: (v * (1 - p) if c in anach_cids else v) for c, v in full.tiers.items()}
    gains = {c: (g * (1 - p) if c in anach_cids else g) for c, g in full.gains.items()}
    return LabelSet(f"human_p{p:.2f}", tiers, gains)


def main():
    recs, base_ids = load_pool()
    full, _, _ = labels()
    ranks = rankings(recs)
    rec_by = {r["cid"]: r for r in recs}

    # Anachronism set over the entire labeled population (the honeypots a human catches).
    anach_cids = {c for c, r in rec_by.items()
                  if r.get("cand") and is_anachronistic(r["cand"])}
    print(f"anachronism honeypots in pool: {len(anach_cids)} / {len(rec_by)}")

    rankings_to_score = {
        "golden": list(base_ids),
        "fusion-raw": build_top(recs, ranks, "raw"),
        "fusion-guard": build_top(recs, ranks, "guarded"),
        "fusion-clean": build_top(recs, ranks, "clean"),
    }

    print(f"\n{'penalty p':>10} " + "".join(f"{k:>14}" for k in rankings_to_score))
    print(f"{'(human-':>10} " + "".join(f"{'composite':>14}" for _ in rankings_to_score))
    print(f"{'aversion)':>10}")
    winners = {}
    for p in (0.0, 0.10, 0.25, 0.40, 0.50, 0.75, 1.0):
        ls = penalized_labels(full, anach_cids, p)
        comps = {k: evaluate(v, ls).composite for k, v in rankings_to_score.items()}
        win = max(comps, key=comps.get)
        winners[p] = win
        row = "".join(f"{comps[k]:>14.4f}" for k in rankings_to_score)
        mark = f"   <- {win}"
        print(f"{p:>10.2f} {row}{mark}")

    print("\n--- READING ---")
    print(f"p=0.00 (raw proxy) winner:        {winners[0.0]}")
    # find crossover where golden or clean overtakes fusion-raw
    for p in (0.10, 0.25, 0.40, 0.50, 0.75, 1.0):
        if winners[p] != "fusion-raw":
            print(f"fusion-raw stops winning at p={p:.2f} (winner: {winners[p]})")
            break
    best_clean_p = [p for p, w in winners.items() if w == "fusion-clean"]
    if best_clean_p:
        print(f"fusion-clean (novel, honeypot-free) is overall best at p in {best_clean_p}")
    else:
        print("fusion-clean never overall best; under human labels golden is the safe ship")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
