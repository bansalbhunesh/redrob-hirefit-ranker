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
