# Experiment Ω — Causal, Integrity-Constrained, Distributionally-Robust Ranking

**Automatic decision: `NO_RANKING_DOMINATES`.**

Ω is not another scorer. It is a decision system that (1) measures latent candidate
quality and integrity with uncertainty from *pairwise* judgments via a hierarchical
Bradley-Terry model, (2) estimates the *causal* penalty of revealing impossible dates,
and (3) selects among candidate rankings by **minimum worst-case regret across a space of
judge-utility worlds**, under hard probabilistic integrity constraints. Golden
(`af8f2b32`) and all prior outputs are untouched.

## 0. Honesty boundary (decisive — read first)

**There are no human reviewers in this environment.** Every "judgment" is produced by a
parameterised reviewer *simulation* whose ground truth is quality = blind-tier and
integrity-violation = anachronism severity. Therefore:

- The fitted posteriors and the causal date-effect are conditional on the simulation's
  assumptions, **not** real human data.
- The judge-utility "world" axis `λ` (how strongly integrity is penalised) is exactly the
  unresolved **(A)/(B) fork** re-expressed as a continuous parameter. Ω **formalises** the
  fork; it cannot **resolve** it — only a real human panel can.
- The `SHIP_OMEGA` gate "beats golden on the **real** human lockbox" is therefore **unmet
  by construction**, so the decision function can only emit `SHIP_GOLDEN`,
  `SHIP_CONSTRAINED_FUSION`, or `NO_RANKING_DOMINATES`. It never claims `SHIP_OMEGA` on
  simulated data.

What Ω genuinely delivers: the complete, runnable apparatus the spec requires, plus a
structural result — the minimax-regret geometry of the decision — that holds regardless of
the simulation details.

## 1. Pipeline

```
178-panel ─▶ freeze: discovery(84) / calibration(28) / untouched-lockbox(66)
candidate ─▶ research variants: original | date_hidden | date_normalized |
             skills_only | career_only | integrity_evidence
simulated reviewers (worlds vary integrity-sensitivity; no reviewer sees two
   variants of one candidate) ─▶ pairwise prefs + integrity severity + confidence
   ─▶ hierarchical Bradley-Terry (reviewer random effects, bootstrap intervals)
   ─▶ per-candidate quality & integrity posteriors with uncertainty
causal: original vs date_normalized across independent reviewer groups × prior sweep
ranking: worst-case utility (quality lower-bound − λ_max·integrity) + hard-integrity
   exclusion ─▶ Ω robust ranking
decision: minimax regret over λ∈[0,2] for {golden, constrained_fusion, fusion_raw, Ω}
   + ship-gate battery ─▶ verdict
```

## 2. Measurement model (validation of the approach)

Hierarchical BT fit on discovery+calibration; **Soft-Pairwise-Accuracy on the untouched
lockbox = 0.789**, and **0.762 after reviewer-family deletion** (drop 1/3 of reviewers) —
the latent-quality recovery is accurate and stable, not a majority-vote artifact. Posteriors
(mean + 10/90 bootstrap interval per candidate) are in `omega_outputs/posteriors.json`.

## 3. Causal date-reveal effect (and why it is circular)

Comparing flagged candidates' win-rate under *original* vs *date-normalized* conditions
across independent simulated reviewer groups, swept over integrity priors:

| integrity prior | win-rate (original) | win-rate (date-normalized) | causal penalty |
|---|---|---|---|
| 0.2 (humans barely care) | 0.27 | 0.00 | −0.27 |
| 0.8 (moderate) | 0.29 | 0.00 | −0.29 |
| 1.6 (strict) | 0.15 | 0.00 | −0.15 |

A penalty appears at every prior — **but this is injected by the simulation's
integrity-sensitivity, not discovered.** It demonstrates the estimator works; it cannot tell
us the *real* human penalty. That is the point of §0: the magnitude is unknowable here.

## 4. Minimax-regret frontier — the structural result

DCG-style human utility of each ranking across 21 worlds `λ∈[0,2]`, `u_λ(c)=quality(c)−λ·integrity(c)`:

| | λ=0 (pure quality / world B) | λ=2 (strict integrity / world A) | **max regret** |
|---|---|---|---|
| golden | 18.26 (best) | **−13.56** | **34.46** |
| constrained_fusion | 17.07 | 17.07 (flat, no violations) | **3.83** |
| fusion_raw | (highest quality) | worst (62 honeypots) | 37.63 |
| Ω robust | 20.91 | 20.91 | **0.00** (by construction) |

**Golden is the best ranking only for `λ < 0.10`** — i.e. only if human judges almost
entirely ignore impossible dates. For *any* meaningful integrity-aversion, golden is
dominated (its 52 honeypots are punished, score → −13.6 at λ=2). Constrained fusion is flat
(zero violations) and has far lower max-regret (3.83 vs 34.46). Ω has zero regret across all
worlds — **but only because it is built from the same quality/integrity estimates used to
define the worlds** (the circularity §0 warns about), which is exactly why its ship-gate
requires independent human confirmation that does not exist.

Frontier + regrets: `omega_outputs/minimax_regret_frontier.json`.

## 5. Ship-gate battery & decision

| Ω ship-gate | result |
|---|---|
| beats golden on **real** human lockbox | **FAIL** (no human data exists) |
| lower worst-case regret than golden | PASS (0.00 < 34.46) |
| not driven by a few candidates (top-5 influence) | PASS |
| stable under reviewer-family deletion | PASS (SPA 0.789→0.762) |
| zero high-conf hard honeypots in top-10 **and** top-100 | PASS (0 / 0) |

Four of five gates pass, but the **only one that matters for trusting a by-construction
result — independent human confirmation — fails by construction.** Among the *confirmable*
options, neither dominates: **golden wins the λ<0.10 slice (world B); constrained_fusion
wins everywhere above it (world A).** The crossover is the (A)/(B) fork. Hence:

> **Decision = `NO_RANKING_DOMINATES`.** The minimax-optimal ranking (Ω) cannot be confirmed
> without a real human integrity panel; absent it, the golden-vs-constrained choice is
> exactly the unresolved question of how much human judges penalise impossible dates.

`omega_outputs/decision.json` carries the machine-readable verdict, gates, regrets, and
partition sizes.

## 6. What Ω adds to the prior conclusion

The earlier phases recommended **ship golden** and flagged the (A)/(B) fork. Ω sharpens this
with a quantitative warning the prior analysis lacked: **golden is minimax-optimal only if
human integrity-aversion is essentially zero (`λ<0.10`).** That is a narrow assumption. If
there is any real chance human judges penalise impossible dates, the integrity-constrained
ranking carries far lower regret. This does **not** change the *action* (golden remains the
EV-max default and the only byte-locked submission), but it raises the value of the **one
experiment that resolves everything** — the frozen human integrity panel — from "nice to
have" to "the single highest-leverage data acquisition available."

## 7. Outputs (`experiments/omega_outputs/`)

`posteriors.json` (per-candidate quality/integrity + intervals), `causal_effects.json`,
`minimax_regret_frontier.json`, `decision.json`, `omega_submission.csv` (robust ranking,
gitignored — candidate data). Reproduce: `omega_lib.py`, `omega_run.py` (deterministic,
`PYTHONHASHSEED=0`, CPU-only, offline).
