# Defend-your-work — Stage 5 interview prep

*Everything here is backed by committed code/docs. Walk the architecture, then field the hard questions.*

## 30-second architecture
`rank.py` = BM25 lexical retrieval + a deterministic 33-feature recruiter matrix (skills, production
evidence, IR/ranking depth, seniority, availability) with multiplicative honeypot/JD-disqualifier
guardrails. CPU-only, offline, no LLM in the ranking path. The **shipped** file is the severity-gated
**hedge** — a deterministic post-hoc Copeland rerank of that pool that *excludes egregious
impossible-tenure candidates*. Reasoning is generated from real profile facts. Output: top-100 CSV.

## The hard questions, answered
**Q: Why a hand scorer, not a modern cross-encoder / LightGBM reranker?**
We built them — 25 method families including LambdaMART, cross-encoders, stacking, learned rerankers.
On a leak-safe holdout *every one lost* to the deterministic scorer (an LGBM hits 0.9474 in-sample but
collapses to 0.8467 held-out). It's a **label-fidelity ceiling, not a model gap** — receipts in
`EXHAUSTIVE_SEARCH.md` / `CROSS_ENCODER_FINDINGS.md`. We ship the simple model *because* we measured the
complex ones.

**Q: Your integrity choice excludes some high-scoring candidates — why?**
The dataset plants impossible-tenure "honeypots" (spec: tier-0, a Stage-3 DQ filter). We face an
(A)/(B) fork: chase the score on anachronistic candidates, or exclude them. We chose the
integrity-safe (A) hedge. It carries **fewer** anachronism candidates than the golden baseline (44 vs
52), **0 honeypots** in the top-100, and an **independent recruiter confirms it** (best of our artifacts
on the blind-recruiter holdout). The flags are **assistive** — "human should verify," never "this is
fraud" (`integrity_cards.py` forbids fraud claims).

**Q: Isn't your evaluation just proxy labels?**
Yes, and we say so everywhere — no official hidden labels existed pre-submission. But we validated
against a **real recruiter's published labels**: our ranking orders the blind recruiter at NDCG@10 0.90,
and the hedge **beats the golden baseline on all 9 measurable label worlds** (7 LLM-judge sets + blind
arbiter + 2 human recruiter sets). And we're **#1 on the proxy vs a 20-repo competitor sample**.

**Q: How do you know it reproduces?**
`rank.py` reproduces golden `af8f2b32` byte-for-byte in 161s, deterministic (BLAS+hashseed pinned),
offline (`docker --network none`). The hedge regenerates from committed scripts
(`_build_pool.py` → `build_hedge_submission.py`) — byte-identical, no manual edits. Gate-locked by
`tests/test_submission_gate.py`.

## Numbers to have ready
- Composite (blind proxy): hedge **0.8748** vs golden 0.8625; beats golden **9/9** label worlds.
- Runtime **161s** / 100K, **6.1 GB** peak, CPU-only, offline. **198 tests**, 0 skipped.
- **0 honeypots** in top-100 (DQ line is 10%). Real-recruiter NDCG@10 **0.90**.

## Live demo to walk (90s)
HuggingFace Space → upload a pool → tiered shortlist → click a candidate → fit breakdown + **decision
verdict (CONTINUE/VERIFY)** → download CSV. That's the recruiter loop end-to-end.
