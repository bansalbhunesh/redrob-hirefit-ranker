#!/usr/bin/env python3
"""Held-out validation of the top-100 consensus swaps (read-only).

docs/top100_ordering_audit.md found 61 swaps improving the composite under all
three label sources simultaneously — but screening 4,950 pairs against the
same three correlated proxies and reporting their aggregate is selection under
multiple comparisons. Decision rule (recorded before this run): adopt nothing
unless the gain survives evaluation on a judge that played no part in
selecting the swaps.

Design:
  Arm A: select swaps on (independent + judge1) only; greedy non-overlapping
         application; evaluate the applied ordering on judge2, untouched by
         selection. Per-swap held-out deltas reported, not just aggregates.
  Arm B: the crossover — select on (independent + judge2), hold out judge1.

Honest scope note: judge1 and judge2 scored the SAME 249 candidate ids, so
this holds out the RATER, not the sample (kappa 0.935 between them). There is
no truly held-out label sample for the top-100; surviving this test means
"survives an independent rater family", which is the strongest test available
locally.

Math check: a from-scratch composite implementation (no project imports)
recomputes every before/after number and is asserted against the harness
path to 1e-9; the largest single swap's NDCG@50 arithmetic is printed
term-by-term for hand verification. A linear-gain DCG variant is also
reported so the conclusion is visibly not an artifact of the exponential
gain convention.

submission.csv is not modified by this script.
"""

from __future__ import annotations

import math
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from redrob_ranker.eval_harness import load_labels, load_submission  # noqa: E402
from top100_ordering_audit import FastScorer  # noqa: E402

SOURCES = [
    (ROOT / "artifacts" / "independent_labels_100k.jsonl", "independent"),
    (ROOT / "docs" / "llm_judge_eval_labels.jsonl", "judge1"),
    (ROOT / "docs" / "llm_judge_eval_2_labels.jsonl", "judge2"),
]


# ---------- independent composite implementation (no project imports) ----------

def _dcg(gains, k, exponential=True):
    total = 0.0
    for i, g in enumerate(gains[:k], start=1):
        num = (2.0 ** g - 1.0) if exponential else g
        total += num / math.log2(i + 1)
    return total


def independent_composite(ranked, gains_map, tiers_map, exponential=True):
    """Challenge composite, policy=exclude, semantics per the harness docstring:
    ideal DCG over the whole label set; MAP denom min(total_relevant, n_scored);
    P@10 and MAP relevance threshold tier >= 3."""
    scored = [c for c in ranked if c in tiers_map]
    g = [gains_map[c] for c in scored]
    ideal = sorted(gains_map.values(), reverse=True)
    ndcg10 = _dcg(g, 10, exponential) / _dcg(ideal, 10, exponential)
    ndcg50 = _dcg(g, 50, exponential) / _dcg(ideal, 50, exponential)
    total_relevant = sum(1 for v in tiers_map.values() if v >= 3.0)
    hits, psum = 0, 0.0
    for i, c in enumerate(scored, start=1):
        if tiers_map[c] >= 3.0:
            hits += 1
            psum += hits / i
    mapv = psum / min(total_relevant, len(scored))
    p10 = sum(1 for c in scored[:10] if tiers_map[c] >= 3.0) / 10
    return 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * mapv + 0.05 * p10


# ------------------------------- arm machinery -------------------------------

def select_swaps(shipped, selection_scorers):
    base = {sc.name: sc.composite(shipped) for sc in selection_scorers}
    out = []
    for i, j in combinations(range(100), 2):
        a, b = shipped[i], shipped[j]
        if not all(a in sc.tiers and b in sc.tiers for sc in selection_scorers):
            continue
        if all(sc.gains.get(a) == sc.gains.get(b) and sc.tiers.get(a) == sc.tiers.get(b)
               for sc in selection_scorers):
            continue
        swapped = list(shipped)
        swapped[i], swapped[j] = swapped[j], swapped[i]
        deltas = []
        ok = True
        for sc in selection_scorers:
            d = sc.composite(swapped) - base[sc.name]
            if d <= 1e-12:
                ok = False
                break
            deltas.append(d)
        if ok:
            out.append((sum(deltas) / len(deltas), i, j))
    return out


def greedy(swaps):
    swaps = sorted(swaps, reverse=True)
    used, picked = set(), []
    for mean_d, i, j in swaps:
        if i in used or j in used:
            continue
        used.update((i, j))
        picked.append((mean_d, i, j))
    return picked


def run_arm(name, shipped, sel_scorers, holdout_sc):
    print(f"\n===== ARM {name}: select on "
          f"({' + '.join(sc.name for sc in sel_scorers)}), "
          f"hold out {holdout_sc.name} =====")
    candidates = select_swaps(shipped, sel_scorers)
    picked = greedy(candidates)
    print(f"selection-consensus swaps: {len(candidates)}; "
          f"greedy non-overlapping applied: {len(picked)}")

    base_held = holdout_sc.composite(shipped)
    pos = neg = zero = 0
    print(f"{'swap':<12} {'sel mean':>9} {'held-out':>9}")
    for mean_d, i, j in picked:
        solo = list(shipped)
        solo[i], solo[j] = solo[j], solo[i]
        hd = holdout_sc.composite(solo) - base_held
        mark = "+" if hd > 1e-12 else ("-" if hd < -1e-12 else "0")
        if mark == "+":
            pos += 1
        elif mark == "-":
            neg += 1
        else:
            zero += 1
        print(f"{i + 1:>4}<->{j + 1:<5} {mean_d:>+9.4f} {hd:>+9.4f}  {mark}")

    applied = list(shipped)
    for _, i, j in picked:
        applied[i], applied[j] = applied[j], applied[i]
    agg_held = holdout_sc.composite(applied) - base_held
    print(f"per-swap held-out signs: +{pos} / -{neg} / 0:{zero}")
    print(f"AGGREGATE held-out ({holdout_sc.name}) delta: {agg_held:+.4f}")

    # Independent math check on the held-out aggregate (exp + linear gains).
    ind_base = independent_composite(shipped, holdout_sc.gains, holdout_sc.tiers)
    ind_applied = independent_composite(applied, holdout_sc.gains, holdout_sc.tiers)
    assert abs((ind_applied - ind_base) - agg_held) < 1e-9, "math check FAILED"
    lin = (independent_composite(applied, holdout_sc.gains, holdout_sc.tiers, exponential=False)
           - independent_composite(shipped, holdout_sc.gains, holdout_sc.tiers, exponential=False))
    print(f"independent recomputation matches (1e-9); "
          f"linear-gain variant of the held-out delta: {lin:+.4f}")
    return picked, applied, agg_held


def main() -> None:
    shipped = load_submission(ROOT / "submission.csv")
    sets = {name: load_labels(p, name) for p, name in SOURCES}
    sc = {name: FastScorer(ls) for name, ls in sets.items()}

    # Harness-vs-independent base check on all three sources.
    for name, s in sc.items():
        ref = s.composite(shipped)
        ind = independent_composite(shipped, s.gains, s.tiers)
        assert abs(ref - ind) < 1e-9, f"base math check failed on {name}"
        print(f"base composite {name:<12} {ref:.4f}  (independent recomputation matches)")

    picked_a, applied_a, agg_a = run_arm(
        "A", shipped, [sc["independent"], sc["judge1"]], sc["judge2"])
    picked_b, applied_b, agg_b = run_arm(
        "B", shipped, [sc["independent"], sc["judge2"]], sc["judge1"])

    # Hand-verification exhibit: largest single swap of arm A, NDCG@50 terms.
    if picked_a:
        _, i, j = max(picked_a)
        a, b = shipped[i], shipped[j]
        s2 = sc["judge2"]
        ga, gb = s2.gains.get(a), s2.gains.get(b)
        print(f"\nhand-check exhibit (arm A largest swap, judge2 gains): "
              f"ranks {i + 1}<->{j + 1}")
        print(f"  gains: {a}={ga}, {b}={gb}")
        if i < 50 and j < 50 and ga is not None and gb is not None:
            d50 = ((2 ** gb - 1) - (2 ** ga - 1)) * (
                1 / math.log2(i + 2) - 1 / math.log2(j + 2))
            print(f"  raw NDCG@50 numerator change = "
                  f"((2^{gb}-1)-(2^{ga}-1)) * (1/log2({i + 2}) - 1/log2({j + 2})) "
                  f"= {d50:+.4f} (divide by ideal DCG@50 = {s2.ideal50:.4f}, "
                  f"x0.30 weight)")

    print("\nsummary:")
    print(f"  arm A held-out (judge2) aggregate: {agg_a:+.4f}")
    print(f"  arm B held-out (judge1) aggregate: {agg_b:+.4f}")
    survives = agg_a > 0 and agg_b > 0
    print(f"  verdict: {'SURVIVES held-out evaluation in both arms' if survives else 'DOES NOT survive — mined noise; the freeze holds'}")


if __name__ == "__main__":
    main()
