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
