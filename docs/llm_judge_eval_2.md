# LLM-Judge Evaluation #2 — second model family (dev-only)

Follow-up to docs/LLM_JUDGE_EVAL.md. Same rubric, same curated field subset, and the
**exact same 249 candidate ids** as judge #1 (gemini-2.5-flash), re-judged by a second,
independent model family so the evaluation cannot be an artifact of one judge's biases.

- Judge #2 model: `openai/gpt-4.1-mini` (OpenAI-compatible gateway), 2026-06-10.
- Driver: `scripts/llm_judge_second.py` (resumable; judges exactly the judge-1 id set).
- Raw labels committed: `docs/llm_judge_eval_2_labels.jsonl`.

## Inter-judge agreement (n = 249)

| statistic | value |
|---|---|
| exact tier agreement | 0.679 |
| within-1 agreement | **1.000** |
| Pearson r | 0.943 |
| quadratic-weighted kappa | **0.935** |
| mean tier | j1 = 2.56, j2 = 2.68 |

No disagreement exceeds one tier anywhere in the sample. By Landis-Koch convention,
kappa 0.935 is "almost perfect" agreement between independent rater families.

## Shipped submission scored under judge #2 (shared harness)

```text
NDCG@10 : 1.0000      NDCG@50 : 0.8191
MAP     : 0.9771      P@10    : 1.0000
COMPOSITE: 0.9423     top-10 tiers: [5,5,5,5,5,5,5,5,5,5]
```

Judge #1 scored the same submission 0.8959 with top-10 tiers [5,5,4,4,5,...]; judge #2
rates those same two contested picks (ranks 3-4) tier-5. The judges disagree about
whether ranks 3-4 carry a "minor gap", not about whether they belong — and neither
judge places anything below tier 4 in the top-10.

## Implications recorded

1. **Top-10 ordering stands.** Reordering to please judge #1's two tier-4s would be
   tuning to one judge's quibble against the other judge's perfect score; there is no
   cross-judge consensus for any swap (see Phase-D note in the challenger gate).
2. The validation story is no longer single-judge: two model families, near-perfect
   ordinal agreement, composites 0.8959 / 0.9423 on a 249-candidate stratified sample.
3. These labels join judge #1 and the independent heuristic labels as the third
   scoring source in the pre-registered LTR challenger gate
   (docs/ltr_challenger_gate.md, committed before any challenger run).
