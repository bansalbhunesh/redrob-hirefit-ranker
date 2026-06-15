# Experiment Ψ — Minimal Human Integrity Calibration (frozen instrument)

The research has reached a legitimate endpoint: model space, deterministic-feature space,
fusion, judge-dependence, candidate-influence, and the full minimax-regret decision have all
been explored, and golden is preserved. Experiment Ω proved the remaining uncertainty is **not
algorithmic** — it is a single empirical unknown: **how strongly real humans penalise a
decisive integrity contradiction after seeing strong career evidence** (the unknown `λ`; Ω's
crossover is at `λ ≈ 0.10`). Ψ is the minimal instrument that purchases exactly that
information. **No automated ranking experiment should follow Ψ** — further automated
optimisation would only re-learn the simulation's assumptions.

This document + the frozen manifest are the instrument. **No human judgments are collected
here** (none are available in this environment); the panel, blinding, pre-registered rule,
and analysis harness are frozen and ready for 9 real reviewers.

## 0. Precise meaning of "golden's 52" (required clarification)

| set | shipped honeypot detector | **anachronism detector** | shipped JD-disqualifier |
|---|---|---|---|
| **golden top-100** | **0** | **52** | 6 |
| 178 research panel | 0 | 96 | 20 |
| full 3000 pool | 0 | (n/a) | 517 |

The "52" are **52 candidates inside golden's top-100 flagged by our separate anachronism
detector** (a claimed technology tenure longer than the technology has existed). By the
**shipped** honeypot detector, golden's top-100 has **0** flags — both statements are true of
different detectors. The 52 are:

- **detector-flagged anomalies** — yes (anachronism detector).
- **confirmed hard contradictions** — *not established* (no ground truth has confirmed them).
- **official planted honeypots** — *unknown* (the ~80 planted IDs are not in our possession;
  overlap unmeasured; a calibrated hard rate is ~0.29% of 100K, hundreds not thousands).

These three are not interchangeable. Ψ exists to move the 52 (specifically the ~5 that drive
the fusion gain) from "anomaly" toward one of the other two categories using real humans.

## 1. Objective

Estimate the **ranking decision**, not a numeric `λ`: do real reviewers behave in the
`λ < 0.10` (golden-preferred) world or the `λ ≥ 0.10` (integrity-constrained) world? The
operational estimand is the **integrity reversal rate** on the influential flagged candidates.

## 2. Panel (frozen: `experiments/psi_panel/manifest.json`, hash `34f43b14a3b40a16`, 24 candidates)

Sampling rule + candidate hashes were frozen **before** any selection on the Ω posterior;
selection uses only pre-Ω signals (hand score, anachronism detector, fusion marginal influence):

| bucket | n | rule |
|---|---|---|
| fusion_gain_drivers | 5 | top-5 anachronism candidates by marginal composite influence (CAND_0094759, 0092278, 0042029, 0033861, 0007411) |
| matched_clean | 5 | nearest hand-score clean candidate to each driver |
| hard_integrity_controls | 4 | highest anachronism severity |
| ambiguous_date_quality | 4 | borderline anachronism severity (~1.0) |
| strong_clean | 3 | top hand score, unflagged |
| weak_clean | 3 | low hand score, unflagged |

## 3. Reviewers

9 reviewers in 3 independent families — **3 recruiters/hiring**, **3 software/AI engineers**,
**3 neutral professionals** familiar with technical resumes. ≥3 judgments per candidate, ideally
one per family. This is not population research; it is to determine whether the shipping
recommendation changes under *real* humans vs the simulated utility function.

## 4. Two-stage blinded design (`reviewer_packet.jsonl`, gitignored)

- **Stage A — career quality (dates & flags hidden):** A1 suitability 0–5; A2 belongs in top-100?;
  A3 supporting evidence; A4 confidence.
- **Stage B — integrity revelation (full original profile):** B1 does the new info materially
  change the decision?; B2 issue class ∈ {noise, incomplete, suspicious, decisive_impossibility};
  B3 remain in top-100?; B4 reject regardless of career quality?; B5 confidence.

Reviewers are never told a candidate was selected by golden, fusion, or Ω.

## 5. Primary metric — integrity reversal rate

`reversal = (initially-selected AND rejected-after-dates) / (initially-selected)`, computed on
flagged candidates, overall **and split by recruiter vs engineer** (the difference is a product
insight):

| reversal | meaning |
|---|---|
| < 20% | humans treat the anomaly as noisy metadata |
| 20–50% | genuine ambiguity; safest conclusion remains unresolved |
| > 50% | integrity concern materially changes selection |
| > 75% | strong evidence for hard exclusion |

## 6. Pre-registered shipping rule (frozen in `psi_analysis.py`)

- **Ship golden iff** no top-100 candidate is a majority-high-confidence hard contradiction
  **and** golden stays human-preferred vs constrained fusion pairwise.
- **Ship constrained fusion iff** it improves human pairwise quality, adds no majority-confirmed
  hard contradiction to the top-10, keeps expected majority-confirmed hard contradictions in the
  top-100 safely below the official threshold, **and** its advantage survives reviewer-family
  deletion.
- **Otherwise** `NO_RANKING_DOMINATES → ship frozen golden` (the preregistered, reproducible
  default — by construction, not by proof of universal superiority).

## 7. Required analyses (and only these)

1 role-quality agreement · 2 integrity agreement · 3 integrity reversal rate (overall + by
family) · 4 golden vs constrained-fusion pairwise preference · 5 reviewer-family deletion · 6
remove-the-five-influential-candidates · 7 decision stability under uncertain labels (bootstrap)
· 8 top-10/top-100 majority-confirmed hard-integrity counts. Transparent counts + bootstrap
intervals — **no over-parameterised model** on a 9-reviewer panel. Harness:
`psi_analysis.py` (validated on a labelled synthetic self-test that reacts correctly to both
worlds; real path reports AWAITING DATA until `responses.jsonl` is filled).

## 8. Stop condition

- Humans clearly penalise the anachronism class → ship the integrity-constrained ranking **only
  if** it passes every quality gate.
- Humans consistently treat the dates as synthetic noise and prefer the recovered candidates →
  constrained fusion becomes defensible.
- Reviewers remain divided → ship golden; report the ambiguity as empirically irreducible.

**After Ψ, no further automated ranking experiment.**

## 9. What to retain from Ω (Stage 4/5 framing)

> We formalised the final submission decision as a minimax-regret problem across plausible
> quality-versus-integrity utilities. Simulated experiments showed the preferred ranking changes
> sharply with the integrity penalty, proving no algorithmic proxy can resolve the decision
> honestly. Because simulated reviewers cannot validate their own assumptions, the system
> correctly refused to declare a winner and identified real human integrity calibration as the
> only remaining high-value information.

## 10. Status

Instrument **frozen and ready**; golden (`af8f2b32`) untouched and reproducible (171 tests).
Awaiting 9 real reviewers. This is the one piece of information that changes the decision — and
the correct next move is to purchase it, not to build another algorithm.
