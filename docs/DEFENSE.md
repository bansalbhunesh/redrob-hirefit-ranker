# Defend V6 — judge and finale preparation

## 20-second answer

HireFit V6 ranks career evidence, contextual fit and behavioral intent—not
keyword lists. It is #1 on our broad public multi-judge benchmarks, processes
the full 100K pool in 136 seconds on two CPUs, explains every rank, emits zero
detected honeypots, and refuses to publish if the input, model, environment or
output drifts.

## Architecture answer

`rank.py --release` runs BM25s plus a deterministic 33-feature recruiter matrix,
seven shallow NumPy heads, feature-only shortlist corrections, multiplicative
behavior/honeypot/disqualifier gates, and grounded reasoning. There is no hosted
LLM, GPU, network dependency, candidate-ID calibration or competitor artifact
in the ranking path.

## The numbers to remember

- Artifact: `8f7f30c6…`; exact 100K membership validated.
- Public field: #1 / 673 mean7; #1 / 100 mean15; #3 / 322 balanced4.
- Versus main: 30 composite wins, 0 ties, 0 losses.
- Reviewer / blind recruiter: 0.8098 / 0.9059.
- Runtime: 136.0 s pipeline / 149.1 s wall, 2 CPU / 16 GiB.
- Integrity: 53 detected, 0 emitted.
- Tests: 262 passed, 6 environment skips.
- Failure attacks: 10,000 corrupt submissions detected; 9,750 invalid configs rejected;
  3-GiB OOM preserves prior output and leaves zero mounted temps.

## Hard questions

**Why not a cross-encoder or large LLM reranker?**

We built and measured modern alternatives—static dense retrieval, learned
weights, LambdaMART, DART-style reranking, cross-encoders, rank fusions and
opposite-direction fusions. Gains that appeared in-sample failed blind or
leave-one-family-out gates. We ship the simpler scorer because it generalized,
not because we avoided complexity.

**Is it really semantic if it is deterministic?**

It interprets the JD through concept expansion, production/retrieval evidence,
career trajectory, title/seniority, role-family depth and HyRE similarity. The
challenge asks for contextual relevance, not a particular model family. On this
synthetic structured pool, heavier semantic models added cost without stable
ranking gain.

**Are these official scores?**

No. Every quality number is labeled as a development/public proxy. The official
weights and hidden labels are unpublished. Our 93.7/100 challenge score is a
transparent mission-derived positioning model, with an honest #1–#3 range.

**What is the strongest evidence against main?**

Fifteen label families under two missing-label policies: V6 wins all 30
composites. A fresh explicit-main run in V6 is byte-identical to origin main,
so the comparison is not caused by accidental baseline drift.

**What if the process crashes or runs out of memory?**

Expensive work stays container-local. Only the verified 40-KB artifact touches
the destination during atomic publish. A forced 3-GiB OOM exited 137, preserved
the existing submission and left zero mounted temporary files.

**Where is V6 weak?**

It is not #1 on every specialist slice: about #14 H2, #115 reviewer and
estimated #20 blind. Those slices trade off sharply across repositories. V6 is
#1 on broad averages, #3 balanced, and Pareto-undominated across the four axes.

## Demo close

> We did not optimize one leaderboard proxy. We built the strongest all-around
> ranking we could reproduce, then engineered the release so a wrong input,
> wrong model, wrong environment, partial write or OOM cannot silently ship it.
