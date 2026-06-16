# Redrob HireFit Ranker

A deterministic, evidence-aware system that ranks the **top 100 of 100,000** candidates for a Senior
AI Engineer role — with receipts for *why* this ranking is the one to ship.

[![Tests](https://img.shields.io/badge/tests-198_passed_0_skipped-brightgreen.svg)](#)
[![Runtime](https://img.shields.io/badge/100K-80s_cloud_·_165s_Docker_2cpu-brightgreen.svg)](#)
[![Execution](https://img.shields.io/badge/CPU--only-offline-blue.svg)](#)
[![Output](https://img.shields.io/badge/output-byte--reproducible-blue.svg)](#)
[![Validation](https://img.shields.io/badge/hedge-2_independent_judges_confirm-success.svg)](#)
[![Decision](https://img.shields.io/badge/decision-SHIP_hedge_·_golden_fallback-success.svg)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Live demo](https://img.shields.io/badge/live_demo-HuggingFace_Space-FBBF24.svg)](https://huggingface.co/spaces/bansal1234/Hirefit)

`Hedge shipped · golden fallback` · `Dashboard available` · `Human lockbox: AWAITING DATA`

---

## ⚡ For judges — the 30-second version

- **What we ship:** a deterministic, CPU-only, byte-reproducible top-100 — the **severity-gated hedge** (`24f84f4b`). Golden (`af8f2b32`) is the **one-command fallback**.
- **Why it's the ship:** beats golden on **7/7** label sets and is confirmed by **two independent cross-family LLM judges it was never tuned against** (gpt-4.1 **+0.0197**, gemini-2.5-pro **+0.0160**); generalizes out-of-sample (16/20 splits). We even built the *higher-composite* alternative and **rejected it** when a blinded integrity judge found its picks not clearly better.
- **The receipts:** **10 alternatives measured and rejected** (cross-encoder, DART, LightGBM, learned weights, embeddings…), **198 tests / 0 skipped**, **0 honeypots** in the top-100, live demos on **HuggingFace + Render**.
- **Honest limit:** ranking quality is label-bound (proven, ~0.878 ceiling for every method) — our edge is **rigor, reproducibility, integrity, and explainability**, not a bigger model.

**Contents:** [Quick start](#quick-start) · [Snapshot](#submission-snapshot) · [Architecture](#architecture) · [What we rejected](#what-we-tried-and-rejected) · [Decision](#the-decision--golden-then-the-hedge) · [Validation](#validation) · [Reproduce](#reproduce) · [Docs](#documentation-map)

## Quick start

```bash
./reproduce.sh        # production gate + shipped-hash check; runs NO research code
```
Runs `rank.py` (which reproduces golden `af8f2b32` byte-for-byte), validates, and checks the shipped
`submission.csv` (the hedge, `24f84f4b`). **Live:** [HuggingFace Space](https://huggingface.co/spaces/bansal1234/Hirefit)
· [Render app](https://redrob-hirefit-ranker.onrender.com) · `streamlit run omega_decision_dashboard.py`
(read-only explanation UI). **Demo video:** _link to be added._

## Submission snapshot

| Property | Verified value |
|---|---|
| Shipped submission | **Severity-gated Copeland hedge** (`24f84f4b`); golden `af8f2b32` = `fallback/golden-af8f2b32` tag |
| Production pipeline | Deterministic `rank.py`, **33-feature** scorer — reproduces golden byte-for-byte |
| Dataset | 100,000 candidates → top-100 |
| Tests | 198 passed, 0 skipped |
| Hedge vs golden (blind arbiter) | composite **0.8748 vs 0.8625**, **beats golden 7/7** — *dev proxy / LLM-audit; **No official hidden labels*** |
| Independent confirmation | gpt-4.1 **+0.0197** · gemini-2.5-pro **+0.0160** (never selected against) |
| Dev-proxy quality | NDCG@10 0.8943 · P@10 = 1.0 — *dev proxy* |
| Runtime | ~80s cloud 2-vCPU · best local Docker ~125s · 165s docker `--cpus=2 --memory=16g` (budget 300s) |
| Memory | peak ~6.1 GB / 16 GB |
| Execution | CPU-only, offline, deterministic (`PYTHONHASHSEED=0`) |
| Integrity | shipped-detector flags in top-100: **0**; anachronism anomalies: **44** (golden 52) |
| Decision | **Ship the hedge** (golden = one-command fallback) |

> The quality rows are **dev proxies** (LLM-audit), explicitly **not** the official hidden score.

## Architecture

`rank.py` reads structured evidence → BM25 lexical base + a 33-feature recruiter matrix → multiplicative
behavioural/honeypot/disqualifier guardrails → deterministic sort → explainable top-100. CPU-only,
offline, byte-reproducible.

![Pipeline architecture](docs/assets/architecture.svg)

## What we tried and rejected

The strongest signal here is everything we **did not** ship — each built, measured against the frozen
100K blind arbiter (frozen before tuning), and rejected on evidence (`docs/measured_negatives.md`).

| Alternative | Measured result on the blind arbiter | Verdict |
|---|---|---|
| Static dense embeddings (potion-32M) | NDCG@10 **+0.0000** at ~2.2× runtime | Rejected |
| Learned logistic-regression weights | composite **0.8238 vs 0.8811** | Rejected |
| LightGBM LambdaMART v2 | composite **−0.031**, NDCG@10 **−0.070** | Rejected |
| LambdaMART v3 (trained on blind labels, leak-safe) | holdout NDCG@10 **−0.040 to −0.104** | Rejected |
| **DART** test-time reranker (ACL 2026) | replicated *above* its paper gain yet **−23% rel** | Rejected |
| Top-K cross-encoder (ms-marco-MiniLM) | in-sample +0.014 → **−0.016 on holdout** | Rejected |
| Rank-space fusion (raw / Copeland) | +0.013 blind — gain from anachronism promotion | Refined into the hedge |

**Conclusion:** the model/trick lever is empty; the bottleneck is feature information + hidden-label
availability, not the model. (Oracle proof: a label-knowing ranker hits 1.0 on the pool; every
label-free method we tried caps at ~0.878.)

## The decision — golden, then the hedge

The shipped submission is **golden's exact top-30, then ranks 31–100 re-drawn by Copeland, excluding
anachronism candidates with severity > 1.2.** Top-10 is byte-identical to golden ⇒ **NDCG@10/P@10
unchanged**; every gain is a better-ordered tail. The hedge carries **fewer anachronism candidates
than golden** (44 vs 52). Production `rank.py` is unchanged; the hedge is a deterministic post-hoc
rerank (`experiments/build_hedge_submission.py`).

![Decision and validation flow](docs/assets/decision_flow.svg)

**Stress-tested, not just chosen.** We built the higher-composite alternative (`rrf` lock-30, 0.8781)
and ran a blinded integrity-aware eval on the candidates that differ: its picks were **not clearly
better** (paired +0.286, 95% CI includes 0, 0 top-rank regressions) → the hedge held. See
`docs/SHIPPING_DECISION.md`, `docs/decisive_integrity_eval.md`.

## Validation

| Study | Result |
|---|---|
| golden vs hedge, 7 label sets (retrospective) | hedge **7/7**, gain entirely NDCG@50/MAP (NDCG@10 identical) |
| out-of-sample holdout (R=20) | **generalizes**: mean **+0.012**, 16/20 splits positive |
| independent judge **gpt-4.1** | composite **+0.0197** |
| independent judge **gemini-2.5-pro** (different lab, integrity-strict) | composite **+0.0160** |
| are the swaps real upgrades? | promoted rated above dropped by **both** judges; 23/36 clean |
| added integrity exposure? | **none** — strict judge flags 32 = 32 in golden and hedge |

Two independent judges from different labs confirm the hedge and agree its swaps are real upgrades
with no added integrity exposure. Full record + per-source data: `docs/golden_vs_hedge_two_studies.md`.

## The integrity distinction

> Detector-flagged anomaly ≠ confirmed hard contradiction ≠ official planted honeypot.

The shipped honeypot detector flags **0** in the top-100; a separate experimental anachronism
detector flags **44** tenure-timeline anomalies (fewer than golden's 52). A downstream, non-ranking
layer maps those to `VERIFY` (human review) — it never asserts fraud and never reorders candidates.

## Reproduce

```bash
./reproduce.sh                       # production gate + shipped-hash check
sha256sum submission.csv             # -> 24f84f4b6160a4bc… (shipped hedge)
# production rank.py reproduces golden af8f2b327f05d30e… (verified by the slice gate)
```
CPU-only, offline, deterministic. Full 100K byte-identical to golden every run: ~80s cloud / ~125s
best local Docker / 165s under `--cpus=2 --memory=16g`, all inside the 300s budget. Details:
`docs/REPRODUCTION.md` · `docs/runtime_matrix.md`.

## Documentation map

- **Decision & validation:** [SHIPPING_DECISION](docs/SHIPPING_DECISION.md) · [golden_vs_hedge_two_studies](docs/golden_vs_hedge_two_studies.md) · [decisive_integrity_eval](docs/decisive_integrity_eval.md) · [best_of_best_meta_study](docs/best_of_best_meta_study.md)
- **What we rejected:** [measured_negatives](docs/measured_negatives.md) · [why_not_reranker](docs/why_not_reranker.md) · [beyond_hedge_sweep](docs/beyond_hedge_sweep.md)
- **Reproduce / runtime:** [REPRODUCTION](docs/REPRODUCTION.md) · [runtime_matrix](docs/runtime_matrix.md) · [SUBMISSION_CHECKLIST](docs/SUBMISSION_CHECKLIST.md)
- **Decision frameworks (research):** Ω [OMEGA_DECISION_SUMMARY](docs/OMEGA_DECISION_SUMMARY.md) · Ψ [PSI_INTEGRITY_PANEL](docs/PSI_INTEGRITY_PANEL.md) · Φ [human_opinion/HUMAN_OPINION_LANDSCAPE](docs/human_opinion/HUMAN_OPINION_LANDSCAPE.md)
- **Program index:** [research/RESEARCH_PROGRAM_INDEX](docs/research/RESEARCH_PROGRAM_INDEX.md)

> Experimental systems (Ω decision framework, Ψ human lockbox, Φ discourse study) are included for
> transparency and do not alter the production ranker. No missing human evidence was simulated.

## License

MIT — see [`LICENSE`](LICENSE). © 2026 Bhunesh Bansal. The bundled competition dataset is not
redistributed and remains the property of Redrob.
