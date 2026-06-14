# Measured Negatives — Alternatives Tested and Rejected

Every alternative below was built, measured against a recorded decision rule, and declined on
the evidence. A measured negative is a strength: it shows we tested, measured, and rejected
rather than shipping unverified complexity. Nothing here beat the shipped hand-tuned scorer.

| # | Alternative | Result | Verdict |
|---|---|---|---|
| 1 | Static dense embeddings (model2vec/potion-32M) | NDCG@10 **+0.0000** at ~2.2× runtime | Rejected ([artifacts/embedding_gate_result.txt](../artifacts/embedding_gate_result.txt)) |
| 2 | Learned logistic-regression weights | **0.8238 vs 0.8811** composite (loses even on labels that favor it) | Rejected ([learned_weights_appendix.md](learned_weights_appendix.md)) |
| 3 | LightGBM LambdaMART **v1** (our features + recovered structure) | **−0.0061** vs a pre-registered ≥ +0.005 gate | Rejected ([ltr_challenger_study.md](ltr_challenger_study.md)) |
| 4 | Availability-blind hedge | +0.0135 / −0.0008 across label hypotheses; only pays if labels ignore the JD | Declined ([hedge_simulation_study.md](hedge_simulation_study.md)) |
| 5 | Consensus calibration pass | no robust gain | Rejected in favor of depth scoring |
| 6 | LightGBM LambdaMART **v2** (pessimistic labels + RUM hard negatives, NDCG@50 objective) | **−0.031 composite on the 100K blind set** (NDCG@10 −0.070, NDCG@50 +0.014); looked good only on a curated 249-candidate LLM-judge sample | Rejected ([why_not_reranker.md](why_not_reranker.md)) |

## The pattern
Two learned rerankers (#3, #6) and two learned/feature alternatives (#1, #2) were measured
against independent labels. **All failed.** The hand-tuned linear scorer with multiplicative
behavioral / honeypot / disqualifier guardrails is the only approach that survived independent
validation — and it is what ships (`submission.csv`, golden-hash locked).

**The 100K frozen blind set (`artifacts/h2_availblind_labels.jsonl`) is the arbiter.** It is
full-population and was frozen before any tuning; proxy/curated samples that disagreed with it
(notably the v2 reranker's four-LLM-judge wins on 249 candidates) did not generalize.
