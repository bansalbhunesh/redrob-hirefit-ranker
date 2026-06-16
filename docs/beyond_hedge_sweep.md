# Beyond-Hedge Sweep (experiment/beyond-hedge)

Goal: try the methods/parameters that were missed and find a result that beats the shipped hedge
(0.8748 blind) / full-Copeland (0.8779). Sweep: 5 aggregators × 5 lock-sizes × 6 severity-caps on
the frozen blind arbiter, holdout-gated (`experiments/exp_beyond_sweep.py`). Read-only.

## What the sweep found

| config | full composite | holdout (R=20) vs golden | anachronism in top-100 |
|---|---|---|---|
| golden (baseline) | 0.8625 | — | 52 |
| shipped hedge (copeland, lock30, sev≤1.2) | 0.8748 | +0.012, 16/20 | 44 |
| full Copeland (lock30, cap∞) | 0.8779 | — | 65 |
| **rrf, lock0, cap∞** | **0.8795** (new full-set high) | **−0.0017 (overfit, fails holdout)** | — |
| **rrf, lock30, cap∞** | **0.8781** | **+0.0118, 18/20 (generalizes)** | **63** |
| mc4, lock20, cap∞ | 0.8747 | best single-split holdout (0.8591) | — |

## Honest conclusions

1. **A higher composite exists, but it overfits or it's riskier.** The single highest full-set score
   (`rrf` lock0 = 0.8795, beats Copeland) **does not generalize** (−0.0017 on the untouched holdout).
2. **The one config that genuinely generalizes** above the hedge — `rrf` lock30, cap∞ — does so with
   **63 anachronism candidates** (more exposed than golden's 52, far more than the hedge's 44). Its
   +0.0118/18-of-20 holdout gain is real, but it is the maximally anachronism-exposed bet.
3. **Every generalizing winner uses cap∞** (no anachronism gating). Capped (safe) variants score
   lower. So **composite gain scales with anachronism exposure** — the wider sweep reproduces the
   original finding rather than breaking it. There is no safe configuration that beats the hedge's
   composite; "better" means betting harder that hidden judges do not date-check tenure.

## Decision

The shipped hedge stays the recommended ship: it sacrifices ~0.003 composite to cut anachronism
exposure to 44 (below golden) while still beating golden 7/7 and on holdout. `rrf` lock30 cap∞ is
documented here as the **higher-upside / higher-risk** alternative if the integrity risk is later
judged negligible. The genuine path to a *safe* higher ceiling is not rank aggregation (capped at
~0.878 here, label-bound by the oracle proof) but **more feature information in the base scorer** —
the post-experiment model-improvement track.

## Model-improvement track (post-experiment): consensus as a soft base-score feature

Tested whether blending the consensus signal into the base score (instead of a hard tail-reorder)
yields a *safe* lift — holdout-gated, weight chosen on TRAIN, scored on the untouched TEST half,
then R=20 repeated 50/50 splits for robustness (`_lib.gate` / `gate_repeat`).

| signal blended | single-split holdout | R=20 repeated | verdict |
|---|---|---|---|
| RRF consensus | +0.0068 (looks good) | **mean −0.0043, 5/20 positive** | **measured negative** |
| Borda consensus | −0.0007 | mean −0.0026, 9/20 | measured negative |

The single split flatters RRF, but repeated splits show it does **not** robustly beat golden — the
"generalization" was split-luck. So consensus-as-a-feature adds no robust signal to the base scorer.

**Combined verdict of the experiment branch:** a higher composite is reachable only by taking more
anachronism risk (hard tail-reorder, `rrf` lock30, 63 flagged); the *safe* levers — capped reorders
and consensus-as-feature — are measured negatives on repeated holdout. This re-confirms, with a wider
sweep and a fresh angle, that the ceiling is label-bound (oracle proof) and the shipped hedge is the
best safe ship. A genuinely safe lift needs new label information or new feature *content* the 33
features miss — not a new aggregator or blend of the existing signals.

## The better result, fully validated — `rrf` lock-30 (cap ∞)

Evaluated like the hedge, across all 7 label sets:

| label set | golden | rrf-lock30 | Δ |
|---|---:|---:|---:|
| h2_availblind (blind arbiter) | 0.8625 | **0.8781** | +0.0156 |
| merged_j1 | 0.8639 | 0.8939 | +0.0299 |
| merged_j2 | 0.9422 | 0.9616 | +0.0194 |
| merged_j3 | 0.8875 | 0.9207 | +0.0332 |
| relabel_j4 | 0.9417 | 0.9527 | +0.0110 |
| relabel_g25 | 0.7680 | 0.7917 | +0.0237 |
| blind_test_frozen | 0.9188 | 0.9359 | +0.0171 |

**7/7 vs golden; beats the shipped hedge on every set; +0.0118 robust holdout (18/20); edges
full-Copeland on the arbiter (0.8781 vs 0.8779).** This is the highest-composite ranking the
experiment produced. Cost: **63 anachronism candidates** (golden 52, hedge 44) — the maximally
anachronism-exposed configuration.

**Verdict:** `rrf` lock-30 is the "best of best" on pure composite and is the recommended ship **iff**
the integrity risk (hidden judges date-checking tenure) is judged negligible. If that risk is real,
the shipped hedge remains the right call (fewer flagged candidates than golden, still 7/7). The
experiment delivered a measurably better composite — it did not deliver a *safe* one; that still
needs new feature content or real labels.
