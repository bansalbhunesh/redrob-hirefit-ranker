# V6 challenge positioning

## Bottom line

V6 is the strongest all-around submission we could measure: **#1 / 673** on
the broad seven-judge mean, **#1 / 100** across the revalidated strongest-union
mean15, and **#3 / 322** on equal four-axis balance. It also wins **30 / 30**
composite comparisons against main and couples that ranking with a fail-closed,
OOM-safe, hash-pinned release.

The official India Runs page defines the mission but does **not** publish
numeric judging weights. Therefore the score below is an explicit
mission-derived positioning model, not an official rubric, score, or result.

Official source: https://hack2skill.com/event/india_runs/

## Mission-derived scorecard

The weights follow the order and emphasis of the official brief: accurate and
expert ranking first; deep job/context understanding and signal integration;
then speed, a robust workable proof of concept, code, documentation/results,
and creativity.

| Mission dimension | Weight | V6 score | Weighted | Evidence |
|---|---:|---:|---:|---|
| Ranking accuracy and shortlist quality | 35% | 9.3 | 32.55 | #1 mean7; #1 mean15; #3 balanced4; 30/30 composites over main |
| Deep JD and contextual understanding | 15% | 8.7 | 13.05 | JD compiler, career evidence, seniority, production/retrieval depth, grounded reasons |
| Profile, career, activity and behavioral signals | 15% | 9.6 | 14.40 | 33 named features; behavior/logistics; 53 traps detected and 0 emitted |
| Speed, robustness and workable POC | 15% | 9.8 | 100K in 136.0 s pipeline / 149.1 s wall at 2 CPU / 16 GiB; forced OOM preserves output |
| Code quality and reproducibility | 8% | 9.9 | 262 passing tests; input/model/wheel/output hashes; deterministic Docker release |
| Blueprint, architecture and results | 7% | 9.8 | README, architecture, audits, deck/PDF, machine-readable manifests and comparisons |
| Innovation and creativity | 5% | 8.5 | seven-head rank hedge, evidence-first features, multiplicative integrity gates, clean-room learning |
| **Total** | **100%** |  | **93.7 / 100** | **Projected #1; honest #1–#3 range** |

## Why the range is honest

- Official hidden labels and official weights are unavailable.
- Specialist public systems lead isolated axes: V6 is about #14 on H2, #115
  on the coverage-qualified reviewer slice, and an estimated #20 on the small
  blind-recruiter slice.
- Those specialists trade away broad quality: no measured public artifact
  dominates V6 across H2, mean7, reviewer and blind simultaneously.
- Human judges may assign more credit to novelty or presentation than the
  mission-derived weighting above.

The defensible claim is therefore: **Grand-Champion-caliber and the projected
#1 all-around submission, with a realistic top-three uncertainty band**. It is
not a claim that the official leaderboard has already been won.

## Main versus V6

| Overall evidence | Main | V6 |
|---|---:|---:|
| Mean7 | 0.872686; #11 / 673 | **0.906553; #1 / 673** |
| Mean15 | 0.875238; #27 / 100 | **0.910406; #1 / 100** |
| Equal four-axis balance | 0.832493; #60 / 322 | **0.876596; #3 / 322** |
| Reviewer | 0.710627; #293 / 430 | **0.809768; #115 / 430** |
| Blind recruiter | 0.871825; #51 / 325 | **0.905858; estimated #20 / 325** |
| Release path | historical baseline | **battle-proof, fail-closed, exact-output release** |

## Judge-facing positioning

> HireFit V6 ranks careers, evidence and intent—not keyword lists. It is the
> #1 broad public-benchmark system we could reproduce, returns the exact 100K
> shortlist in 136 seconds on two CPUs, explains every rank, blocks every
> detected trap from the top 100, and fails closed if the input, model,
> environment or output drifts.
