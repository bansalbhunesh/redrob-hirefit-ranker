# Held-Out Validation of the Top-100 Consensus Swaps

Follow-up to docs/top100_ordering_audit.md, run before any adoption decision.
Tool: `scripts/swap_holdout_validation.py`. `submission.csv` unchanged.

## Decision rule (recorded before the run)

The 61-consensus-swap result screened 4,950 pairs against three correlated
proxies — selection under multiple comparisons. Adopt nothing unless the gain
survives evaluation on a judge that played no part in selecting the swaps:
select on (independent + judge 1), evaluate on judge 2 only; then cross over.
Per-swap deltas reported, not just aggregates; every composite independently
recomputed outside the harness (from-scratch implementation, asserted to
1e-9), with a linear-gain DCG variant as a convention-robustness check.

**Scope honesty:** judge 1 and judge 2 scored the *same 249 ids* (kappa
0.935), so this holds out the **rater, not the sample**. It is the strongest
test available locally; "survives" means *survives an independent rater
family*, not *survives held-out data*. No local test can do better without
new labels.

## Results

| | arm A (hold out judge 2) | arm B (hold out judge 1) |
|---|---|---|
| selection-consensus swaps | 97 | 225 |
| greedy non-overlapping applied | 9 | 14 |
| per-swap held-out signs | **+5 / −0 / 0:4** | **+5 / −0 / 0:9** |
| aggregate held-out delta | **+0.0106** | **+0.0086** |
| linear-gain variant | +0.0046 | +0.0033 |

The zeros are rating ties (the held-out judge scores both candidates in the
pair identically), not contradictions. **No selected swap loses on the
held-out judge in either arm.** Mined noise would show negatives; this shows
ties-or-gains only, at 70–90% of the original three-source magnitude (40%
under linear gains — still positive).

## Verdict

**SURVIVES both arms.** The reordering signal is real with respect to every
rater family available, under both DCG gain conventions, with the math
independently verified. By the project's own pre-registered standard (mean
composite +0.005 at full coverage — the bar the LTR challenger failed at
−0.0061), the case for adoption is now: original three-source consensus
+0.0116, held-out rater validation +0.0086 to +0.0106, zero contradicting
per-swap evidence.

## Adoption set, if rolled

The conservative set is the greedy-8 from the original **three-source**
consensus (docs/top100_ordering_audit.md) — strictly stronger than either
arm's two-source selection (e.g., arm A's top pick 4↔37 is a judge-2 tie and
is correctly absent from the three-source set). Any roll follows the full
protocol: monotonic score re-emission, golden-hash roll, fresh Docker
reproduction, honeypot re-check (membership is unchanged, so 0 by
construction), and row-by-row review of ranks 20–60.

## Status

No change adopted in this commit. Awaiting the hash-roll decision.
