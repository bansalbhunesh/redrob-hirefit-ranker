# Why We Ship a Hand-Tuned Scorer, Not a Learned Reranker

**Short version:** we trained two learned rerankers. **Both failed on independent blind
labels.** The hand-tuned linear scorer with multiplicative guardrails is the only approach
that survived independent validation, so it is what ships.

This is a deliberate, evidence-backed decision — not an absence of ML. It demonstrates a
commitment to **blind evaluation over proxy chasing**.

## The two learned rerankers we tested

### v1 — LightGBM LambdaMART challenger (proxy labels)
A LambdaMART model over our own 33 features plus recovered generator structure. Measured at
**−0.0061 composite against a pre-registered ≥ +0.005 gate**, committed before training.
Rejected. Full study: [docs/ltr_challenger_study.md](archive/ltr_challenger_study.md).

### v2 — LightGBM LambdaMART reranker (pessimistic labels + RUM hard negatives)
A retrieve-then-rerank design: the hand pipeline produces guardrailed scores, then a
`lambdarank` model (NDCG@50 objective, 33 features incl. backend_depth / data_bi_depth /
hyre_similarity, trained on pessimistic-judge labels + RUM hard negatives) re-orders the
top-K, with the honeypot multiplier re-applied.

**On LLM-judge proxies (249 curated candidates) it looked good:**

| Judge | Δ composite | Δ NDCG@50 | Δ NDCG@10 |
|---|---|---|---|
| GPT-4.1-mini | +0.027 | +0.085 | 0.000 |
| DeepSeek | +0.085 | +0.137 | 0.000 |
| Claude-3.5-haiku | +0.019 | +0.069 | 0.000 |
| Gemini-3.1-flash-lite | +0.049 | +0.069 | +0.030 |

**On the 100K frozen blind set (`artifacts/h2_availblind_labels.jsonl`, generated before any
tuning, full population) it failed:**

| Metric | Hand (fdfd3f35) | Reranker (0a9c3155) | Δ |
|---|---|---|---|
| composite | **0.8625** | 0.8318 | **−0.0307** |
| NDCG@10 | **0.8288** | 0.7593 | **−0.0695** |
| NDCG@50 | 0.8270 | 0.8404 | +0.0135 |

The reranker improved NDCG@50 (+0.014) but **destroyed NDCG@10 (−0.070)**. Because NDCG@10 is
**50% of the hidden composite**, the net effect was **−0.031 composite**. It reorders the
top-10 in a way the curated LLM-judge sample rewards but the full-population blind set
penalizes — the signature of **proxy overfitting**. Rejected; the hand pipeline is retained.

## The lesson
**Proxy validation is not sufficient. The 100K blind set is the arbiter.** Four independent
LLM judges agreeing on a 249-candidate sample did not generalize to the full population. The
hand-tuned scorer, which never chased a proxy, is the only ranker that has survived every
independent check we have run.

The reranker experiment is preserved in full on the `codex/ndcg50-killer` branch (training,
cross-judge validation, swap analysis) as a documented negative, not deleted.
