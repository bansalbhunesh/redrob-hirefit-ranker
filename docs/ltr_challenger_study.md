# LTR Challenger Study — negative result (gate: FAILED, shipped scorer stands)

Executed exactly once against the pre-registered gate (docs/ltr_challenger_gate.md,
committed before any training run). No re-tuning followed this evaluation.

## The challenger (the strongest realistic rival, built in-house)

- LightGBM LambdaMART (`objective=lambdarank`, deterministic, seed 13, single-thread),
  5-fold out-of-fold so no id is scored by a model that trained on it.
- Features: the shipped 28 features + clamped BM25 + 17 generator-forensics features
  (stated/field/history YoE gaps, company-pool fractions, stratum signature, education
  tiers — docs/generator_forensics.md).
- Training labels: 888 LLM-judged ids (judge #1 + a 639-id gpt-4o-mini expansion across
  all generator strata; judge #2 held out for scoring only) + 6,000 generator-rule
  labels (stratum prior + JD availability adjustment), judged rows weighted 3x.
- Guardrails (behavioral / honeypot / disqualifier multipliers) applied on top,
  identical to shipped.
- Tooling: scripts/ltr_challenger.py, scripts/score_challenger.py;
  raw lists in artifacts/challenger_top100.json (top-100 overlap with shipped: 70/100).

## Gate evaluation (criterion 1: mean composite across three label sources)

| ranking | independent | judge 1 (gemini-2.5-flash) | judge 2 (gpt-4.1-mini) | mean |
|---|---|---|---|---|
| shipped hand-tuned | 0.8811 (100% cov) | 0.8959 (100% cov) | 0.9423 (100% cov) | **0.9064** |
| LTR challenger | 0.8606 (100% cov) | 0.8950 (**75% cov**) | 0.9454 (**75% cov**) | **0.9003** |

**Delta = -0.0061 against a required >= +0.005. The gate FAILS on two grounds:**
the mean composite is lower, and the challenger pushes 30 unjudged candidates into
its top-100, collapsing judge coverage to 75% — the same selection-bias regime the
sensitivity sweep's coverage guard exists to reject.

## Reading the result

- The model's top gains went to `bm25` and `skill_depth_score` — it rediscovered the
  shipped scorer's own backbone, then traded curated top-10 ordering for mid-rank
  shuffling that no label source rewards.
- This is now the **third measured negative result** (after static dense embeddings
  at +0.0000 NDCG@10 / 2.2x runtime, and the learned-LR study at 0.8238 vs 0.8811):
  with one JD, no real outcome labels, and a synthetic pool whose latent structure
  the hand-tuned features already capture, learned weights have nothing left to learn
  — they can only disturb a curated ordering.
- The companion ordering audit (scripts/top10_ordering_audit.py) is consistent: no
  pairwise swap in the shipped top-15 improves NDCG@10 under all covering label
  sources. The frozen submission stands untouched.

## Status

`submission.csv` unchanged; golden hash unchanged. The challenger and its labels are
committed as evaluation evidence only. If Redrob ever has real hire/outcome labels,
this exact pipeline is the path to learned weights — over the same 28 features, with
the same guardrails and audit trail.

## Addendum (2026-06-14): v2 reranker — same conclusion on the 100K blind set

A second, stronger LambdaMART reranker was built on the `codex/ndcg50-killer` branch
(retrieve-then-rerank over the hand top-K, 33 features incl. backend_depth / data_bi_depth /
hyre_similarity, **NDCG@50 objective**, trained on pessimistic-judge labels + RUM hard
negatives, honeypot multiplier re-applied). On a curated 249-candidate **LLM-judge** sample it
looked good (GPT-4.1-mini +0.027, DeepSeek +0.085, Claude-3.5-haiku +0.019,
Gemini-3.1-flash-lite +0.049 composite; held-out-judge CV +0.091 NDCG@50).

Then it was scored on the **100K frozen blind set** (`artifacts/h2_availblind_labels.jsonl`,
generated before any tuning, full population):

| Metric | Hand (fdfd3f35) | Reranker v2 (0a9c3155) | Δ |
|---|---|---|---|
| composite | **0.8625** | 0.8318 | **−0.0307** |
| NDCG@10 | **0.8288** | 0.7593 | **−0.0695** |
| NDCG@50 | 0.8270 | 0.8404 | +0.0135 |

**Why the LLM proxies misled.** The four LLM judges all scored the *same* 249 candidates
curated near the top of the pool — a narrow, correlated slice. The reranker reordered the
top-10 in a way that slice rewarded; on the full 100K population that same reorder *lost*
NDCG@10 (−0.070), and since NDCG@10 is half the composite the net was −0.031. Proxy agreement
on a curated sample is not population generalization.

**Conclusion: proxy validation is not sufficient. The 100K blind set is the arbiter.** This is
the **second** LTR measured negative — v1 at −0.0061 on proxy labels, v2 at −0.031 on the 100K
blind set. The hand-tuned scorer is retained. Full Stage-5 framing:
[why_not_reranker.md](why_not_reranker.md); master list: [measured_negatives.md](measured_negatives.md).
