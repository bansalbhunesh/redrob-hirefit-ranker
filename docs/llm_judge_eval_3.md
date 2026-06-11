# LLM-Judge Evaluation #3 — third model family (dev-only)

Same rubric, same 249 candidate ids as judges #1 (gemini-2.5-flash) and #2
(gpt-4.1-mini), re-judged by `deepseek/deepseek-chat` (2026-06-11) so the
validation rests on three independent model families: Google, OpenAI, DeepSeek.

## Three-family agreement (n = 249, quadratic-weighted kappa / within-1)

| pair | QWK | within-1 |
|---|---|---|
| gemini vs gpt-4.1-mini | 0.935 | 1.000 |
| gemini vs deepseek | 0.918 | 1.000 |
| gpt-4.1-mini vs deepseek | 0.921 | 0.988 |

By Landis-Koch convention all three pairs are "almost perfect" agreement.

## Shipped (post-calibration) submission under judge #3

composite **0.9068**, NDCG@10 0.9432, coverage 100%.

The recitation this enables: three independent judge families, near-perfect
ordinal agreement, composites 0.90-0.94 on the same stratified sample — the
"your judges are correlated" objection now requires all three frontier-model
families to share the same bias. Raw labels committed:
docs/llm_judge_eval_3_labels.jsonl.

## Post-adoption validation of the calibration pass (the test that matters)

Judge #3 was collected *after* the consensus calibration roll (81cb93f) and
played no part in selecting the eight adopted swaps — unlike the crossover
holdout (docs/swap_holdout_validation.md), whose rater families were both used
in screening. Honesty first: measured over all 279 top-100 pairs where the
independent labeler and judge 1 strictly agree, judge 2 contradicts **zero**
(0/279, 7.2% ties), so the crossover holdout had little power to reject a
mined-noise null on its own. Judge #3 is the genuinely out-of-selection rater.

Its verdict, reproducible from committed files
(`eval_harness.evaluate` over `outputs/pre_calibration_submission.csv` vs
`submission.csv` with `docs/llm_judge_eval_3_labels.jsonl`):

- Aggregate: composite **0.8943 → 0.9068, delta +0.0124** — above the
  pre-registered +0.005 adoption bar, from a rater family that did not exist
  at adoption time.
- Per adopted swap: **6 confirm, 1 tie** (CAND_0060054/CAND_0042506, both
  tier 4), **1 contradict** — judge #3 rates CAND_0042100 (tier 5) above
  CAND_0027691 (tier 4), reversing the smallest adopted swap (+0.0002 of the
  +0.0116). That swap is location-driven (CAND_0042100 is Singapore-based;
  the JD prefers Pune/Noida and relocation from Tier-1 Indian cities), a
  ground the LLM judge does not weight the way the JD instructs.
- Judge #3's base contradiction rate on three-source-consensus top-100 pairs
  is 5/259 (1.9%); one contradiction among eight adopted swaps is within
  noise of that base rate.

Recorded so the record argues both ways: one swap is contested by the newest
rater, and the adopted set still clears the adoption bar on that same rater
by 2.5x.
