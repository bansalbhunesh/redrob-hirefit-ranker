# Redrob HireFit Ranker

A deterministic, evidence-aware candidate-ranking system for 100,000 profiles, with a frozen production ranking and a fully audited research program for ranking quality, integrity risk and human uncertainty.

[![Tests](https://img.shields.io/badge/tests-198_passed_0_skipped-brightgreen.svg)](#)
[![Runtime](https://img.shields.io/badge/100K-80s_cloud_·_~125s_local_Docker-brightgreen.svg)](#)
[![Execution](https://img.shields.io/badge/CPU--only-offline-blue.svg)](#)
[![Output](https://img.shields.io/badge/output-byte--reproducible-blue.svg)](#)
[![Production](https://img.shields.io/badge/production_ranking-unchanged-success.svg)](#)
[![Verdict](https://img.shields.io/badge/verdict-NO__RANKING__DOMINATES-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Live demo](https://img.shields.io/badge/live_demo-HuggingFace_Space-FBBF24.svg)](https://huggingface.co/spaces/bansal1234/Hirefit)

`Hedge shipped · golden fallback` · `Dashboard available` · `Human lockbox: AWAITING DATA`

---

## Judge quick start

```bash
./reproduce.sh        # runs the verified production path ONLY
```
This (1) runs the frozen production ranking (`rank.py`, which reproduces the golden baseline
`af8f2b32` byte-for-byte), (2) validates the output, (3) checks deterministic byte-reproduction
of the shipped `submission.csv` (the hedge, `24f84f4b`), and (4) runs **no** research ranking.

```bash
pip install -r requirements-dashboard.txt      # presentation deps only — NOT production
streamlit run omega_decision_dashboard.py
```
The dashboard is a **read-only, judge-facing research & explanation interface** — not the
production ranker. It imports no production scoring code and changes no submission output.

## Submission snapshot (verified from this repo)

| Property | Verified value |
|---|---|
| Shipped submission | **Severity-gated Copeland hedge** (`24f84f4b`) — golden `af8f2b32` retained as the `fallback/golden-af8f2b32` tag |
| Production pipeline | Deterministic `rank.py` — reproduces golden `af8f2b32` byte-for-byte (slice gate + full 100K) |
| Dataset | 100,000 candidates |
| Tests | 198 passed, 0 skipped |
| Hedge vs golden (blind arbiter) | composite **0.8748 vs 0.8625**, **beats golden on 7/7** label sets — *dev proxy / LLM-audit; **No official hidden labels*** |
| Dev-proxy quality | NDCG@10 0.8943 · P@10 = 1.0 — *dev proxy / LLM-audit* |
| Runtime | ~80s cloud 2-vCPU serial · 165s Docker `--cpus=2 --memory=16g` (matrix 124.7–193.4s; budget 300s) |
| Execution | CPU-only, offline, deterministic (`PYTHONHASHSEED=0`) |
| Determinism | shipped `submission.csv` sha256 `24f84f4b6160a4bc…` verified; production reproduces golden `af8f2b327f05d30e…` |
| Shipped-detector flags in top-100 | 0 |
| Experimental anachronism anomalies | **44** (golden carries 52) |
| Final automated verdict | `NO_RANKING_DOMINATES` |
| Submission decision | **Ship the hedge** (golden = one-command fallback) |

> The quality row is a **dev proxy** (LLM-audit), explicitly **not** the official hidden
> competition score. We never claim to know the hidden labels.

## The product in one view

The production system reads structured candidate evidence (skills with durations, dated career
history, education, behavioural signals), scores each candidate with a deterministic hand-tuned
scorer plus multiplicative integrity/behaviour guardrails, and emits an explainable,
byte-reproducible top-100 submission. CPU-only, fully offline, with no network calls and no
model downloads at inference.

## The integrity distinction (read this)

> **Detector-flagged anomaly ≠ confirmed hard contradiction ≠ official planted honeypot.**

- The **shipped honeypot detector** flags **0** candidates in the shipped hedge's top-100
  (verified on `submission.csv`).
- A **separate experimental anachronism detector** flags **44** technology-tenure timeline
  anomalies (e.g. a claimed skill tenure longer than the technology has existed) — **fewer than
  golden's 52**, because the hedge promotes only defensible cases (tenure ≤1.2× the tech's age)
  and excludes the egregious ones.
- Those 44 are **not** confirmed fraud, **not** confirmed hard contradictions, and **not**
  known official planted honeypots (the official planted IDs are unavailable to us).
- A **downstream, non-ranking** integrity layer assigns proportionate states: the 44 anachronism
  anomalies map to `PROBABLE_CONTRADICTION → VERIFY`; the remaining 56 are
  `CLEAR/AMBIGUOUS → CONTINUE/CLARIFY`; **0** are `CONFIRMED_CONTRADICTION → BLOCK`.
- These actions are explanatory and **do not modify the shipped ranking**. `VERIFY` requests
  human review; it never asserts fraud and never reorders candidates.

## What we tried and rejected — measured negatives

The strongest signal in this submission is everything we **did not** ship. Each alternative
below was built, measured against the **frozen 100K blind arbiter**
(`artifacts/h2_availblind_labels.jsonl`, frozen before any tuning), and rejected on the
evidence — not on taste. A measured negative is a strength: it proves the lever is empty.

| Alternative | Measured result on the blind arbiter | Verdict |
|---|---|---|
| Static dense embeddings (potion-32M) | NDCG@10 **+0.0000** at ~2.2× runtime | Rejected |
| Learned logistic-regression weights | composite **0.8238 vs 0.8811** | Rejected |
| LightGBM LambdaMART v2 (NDCG@50 obj.) | composite **−0.031**, NDCG@10 **−0.070** | Rejected |
| LambdaMART v3 *trained on the blind labels themselves* (NDCG@10 obj., leak-safe holdout) | holdout NDCG@10 **−0.040 to −0.104** | Rejected |
| **DART** test-time reranker (ACL 2026) | **replicated the paper (+5.3% rel, beating its own +2.1%)** yet composite **0.649 vs 0.808** (−23% rel) | Rejected |
| Top-K cross-encoder (ms-marco-MiniLM) | in-sample +0.014 → **−0.016 on the untouched holdout** | Rejected |
| Learned interaction features (title×evidence) | single split +0.008 → **noise under 20× repeated holdout** | Rejected |
| New orthogonal features (impact-density, gzip-NCD) | **no train-supported lift** (best train Δ = 0.0000) | Rejected |
| Rank-space Fusion — **clean** (no anachronism promotion) | **−0.0322** holdout (1/20) | Rejected |
| Rank-space Fusion — **raw** | +0.0128 blind, 7/7 judge sets — but **entirely from promoting anachronism-flagged candidates** | Held as the (B) bet, not shipped |

**The pattern (`docs/measured_negatives.md`):** five rerankers, five learned/feature
alternatives, and one rank-space fusion family — **all failed against independent labels.** The
sharpest case (DART) was replicated *above* its published gain and still lost by 23% relative,
because it adapts a dense representation that carries less task signal than the 33 hand-tuned
features. **Conclusion: the model/trick lever is empty; the bottleneck is feature information
content + hidden-label availability, not the model.** That is *why* a deterministic hand-tuned
scorer is the expected-value-maximising ship — a conclusion earned by measurement, not assumed.

## Why the hedge ships (golden retained as fallback)

The shipped submission (`24f84f4b`) is precisely **golden's exact top-30, then ranks 31–100
re-drawn from the pool by Copeland (Condorcet) score, excluding anachronism candidates with
severity > 1.2** (claimed tenure ≤1.2× the tech's age = defensible/rounding; egregious cases
excluded). It is verified byte-identical to golden in order through rank 30 — so **NDCG@10 and
P@10 are unchanged from golden by construction**; every measured gain is a better-ordered *tail*.
Validated head-to-head under one frozen protocol in
[`docs/golden_vs_hedge_two_studies.md`](docs/golden_vs_hedge_two_studies.md).

1. It **beats golden on 7/7 label sets** on the frozen blind arbiter (composite **0.8748 vs
   0.8625**) — all of it NDCG@50/MAP — the advantage **generalizes out-of-sample** on held-out
   label halves (mean +0.012, 16/20 splits positive), and it is **confirmed by two independent
   fresh judges from different labs** the hedge was never selected against (gpt-4.1 +0.0197;
   integrity-strict gemini-2.5-pro +0.0160) — see
   [`docs/golden_vs_hedge_two_studies.md`](docs/golden_vs_hedge_two_studies.md).
2. It carries **fewer anachronism-flagged candidates than golden itself** (44 vs 52), so under a
   modeled anachronism-penalty world its worst case is **better than both golden and full
   Copeland** (`experiments/exp_robust_hedge.py`). It is the rare alternative that lifts proxy
   quality *without* increasing anachronism exposure.
3. It passes the **complete production and firewall suite** (198 tests, 0 skipped); production
   `rank.py` is **unchanged** and reproduces golden `af8f2b32` byte-for-byte (slice gate + full
   100K) — the hedge is a deterministic, audited post-hoc rerank.
4. **The honest residual risk:** the 7 label sets are only ~1.85 effective independent judges,
   and the hedge's gain still comes partly from promoting (defensible) anachronism candidates —
   a bet that loses if the hidden judges date-check tenure. **Golden is also exposed there** (52
   such candidates), and is retained byte-reproducible as the **one-command fallback**
   (`fallback/golden-af8f2b32`) if that risk is judged to dominate.
5. **Ω** used **simulated** reviewer worlds (cannot self-validate); **Ψ** still requires real
   **candidate-specific human** judgments (`AWAITING HUMAN DATA`).

> The hedge ships because it dominates golden on every measured label set while reducing
> anachronism exposure — and because the safer option (golden) is preserved, one command away,
> for the world where tenure date-checking is the deciding signal.

## Research arc (uncertainty reduction, not metric chasing)

```text
Golden → Competitor audit → Learned-model & Cross-Encoder experiments → Rank-space Fusion
  → Judge-dependence & influence audits → Evidence-channel experiments
  → Integrity-constrained Fusion → Ω decision framework
  → Ψ candidate-specific human instrument → Φ public hiring-norms study
  → Rank-space Condorcet (Copeland) → severity-gated hedge → Ship Hedge (golden retained as fallback)
```
Every stage **reduced uncertainty** about what is real; not every stage improved a metric.
Most alternatives are *measured negatives* — built, measured against independent labels, and
rejected on the evidence (`docs/measured_negatives.md`).

## Dashboard preview

`streamlit run omega_decision_dashboard.py` shows, in 30–60 seconds: a `NO_RANKING_DOMINATES`
decision banner · shipping-gate battery · minimax-regret frontier (with a **simulated,
model-specific** λ slider) · the 52-anomaly reconciliation + filterable table · candidate
integrity audit cards · fusion autopsy · Ψ frozen-panel status (`AWAITING HUMAN DATA`) · Φ
real-discourse findings · the complete experiment timeline · and why the hedge ships. It reads
only committed local artifacts; missing artifacts render "Artifact unavailable", never invented
values.

## Documentation map

- [docs/golden_vs_hedge_two_studies.md](docs/golden_vs_hedge_two_studies.md) — golden vs shipped hedge, one frozen protocol, with holdout
- [docs/SHIPPING_DECISION.md](docs/SHIPPING_DECISION.md) · [docs/REPRODUCTION.md](docs/REPRODUCTION.md)
- [docs/PSI_INTEGRITY_PANEL.md](docs/PSI_INTEGRITY_PANEL.md) · [docs/OMEGA_DECISION_SUMMARY.md](docs/OMEGA_DECISION_SUMMARY.md)
- [docs/human_opinion/HUMAN_OPINION_LANDSCAPE.md](docs/human_opinion/HUMAN_OPINION_LANDSCAPE.md) · [docs/COMPETITIVE_LANDSCAPE.md](docs/COMPETITIVE_LANDSCAPE.md)
- [docs/DASHBOARD_GUIDE.md](docs/DASHBOARD_GUIDE.md)
- [docs/research/RESEARCH_PROGRAM_INDEX.md](docs/research/RESEARCH_PROGRAM_INDEX.md) · [docs/research/FINAL_RESULT_CATALOG.md](docs/research/FINAL_RESULT_CATALOG.md) · [docs/research/FINAL_INTEGRATION_REPORT.md](docs/research/FINAL_INTEGRATION_REPORT.md)

## Research boundary

> Experimental systems are included for transparency, auditability and reproducibility. They
> do not alter the frozen production ranking. The remaining unresolved evidence requires real
> humans: the Ψ candidate panel, an independent Φ coder, and verified recruiter/India
> practitioner perspectives. No missing human evidence was simulated or fabricated.

## Reproduce

```bash
PYTHONHASHSEED=0 python -m pytest tests/test_submission_gate.py -q   # production + shipped-hash gate
sha256sum submission.csv                                            # -> 24f84f4b6160a4bc… (shipped hedge)
# production rank.py still reproduces the golden baseline af8f2b327f05d30e… (verified by the slice gate)
```
CPU-only, offline, deterministic. Full path: `docs/REPRODUCTION.md`.

## License

Released under the **MIT License** — see [`LICENSE`](LICENSE). © 2026 Bhunesh Bansal.
The bundled competition dataset is **not** redistributed and remains the property of Redrob.
