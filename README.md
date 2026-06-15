# Redrob HireFit Ranker

A deterministic, evidence-aware candidate-ranking system for 100,000 profiles, with a frozen production ranking and a fully audited research program for ranking quality, integrity risk and human uncertainty.

[![Tests](https://img.shields.io/badge/tests-198_passed_0_skipped-brightgreen.svg)](#)
[![Runtime](https://img.shields.io/badge/100K-80s_cloud_·_~125s_local_Docker-brightgreen.svg)](#)
[![Execution](https://img.shields.io/badge/CPU--only-offline-blue.svg)](#)
[![Output](https://img.shields.io/badge/output-byte--reproducible-blue.svg)](#)
[![Production](https://img.shields.io/badge/production_ranking-unchanged-success.svg)](#)
[![Verdict](https://img.shields.io/badge/verdict-NO__RANKING__DOMINATES-orange.svg)](#)

`Golden frozen` · `Dashboard available` · `Human lockbox: AWAITING DATA`

---

## Judge quick start

```bash
./reproduce.sh        # runs the verified golden production path ONLY
```
This (1) runs the frozen golden production ranking, (2) validates the output, (3) checks
deterministic byte-reproduction of `submission.csv`, and (4) runs **no** research ranking.

```bash
pip install -r requirements-dashboard.txt      # presentation deps only — NOT production
streamlit run omega_decision_dashboard.py
```
The dashboard is a **read-only, judge-facing research & explanation interface** — not the
production ranker. It imports no production scoring code and changes no submission output.

## Submission snapshot (verified from this repo)

| Property | Verified value |
|---|---|
| Production ranking | Frozen golden (`af8f2b32`) |
| Dataset | 100,000 candidates |
| Tests | 198 passed, 0 skipped |
| Dev-proxy quality | NDCG@10 0.8943 · P@10 = 1.0 — *dev proxy / LLM-audit; **No official hidden labels*** |
| Runtime | ~80s cloud 2-vCPU serial · ~125s local Docker serial (budget 300s) |
| Execution | CPU-only, offline, deterministic (`PYTHONHASHSEED=0`) |
| Determinism | golden `submission.csv` sha256 `af8f2b327f05d30e…` verified |
| Shipped-detector flags in top-100 | 0 |
| Experimental anachronism anomalies | 52 |
| Final automated verdict | `NO_RANKING_DOMINATES` |
| Submission decision | **Ship golden** |

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

- The **shipped honeypot detector** flags **0** candidates in golden's top-100.
- A **separate experimental anachronism detector** flags **52** technology-tenure timeline
  anomalies (e.g. a claimed skill tenure longer than the technology has existed).
- Those 52 are **not** confirmed fraud, **not** confirmed hard contradictions, and **not**
  known official planted honeypots (the official planted IDs are unavailable to us).
- A **downstream, non-ranking** integrity layer assigns proportionate states:
  - 45 `CLEAR → CONTINUE` · 3 `AMBIGUOUS → CLARIFY` · 52 `PROBABLE_CONTRADICTION → VERIFY` · 0 `CONFIRMED_CONTRADICTION → BLOCK`
- These actions are explanatory and **do not modify the golden ranking**. `VERIFY` requests
  human review; it never asserts fraud and never reorders candidates.

## Why golden ships

1. It is **frozen and byte-reproducible** (`af8f2b32`).
2. It passes the **complete production and firewall suite** (187 tests, 0 skipped).
3. **Raw Fusion's** proxy gain was **fragile and concentrated** — the 7 label sets are only
   ~1.85 effective independent judges, and 56% of the gain came from 5 anachronism-flagged
   candidates (it inverts to −0.011 without that class).
4. **Ω** formalised the quality-vs-integrity trade-off as a minimax-regret problem but used
   **simulated** reviewer worlds, so it cannot independently validate its own assumptions.
5. **Ψ** still requires real **candidate-specific human** judgments (`AWAITING HUMAN DATA`).

> Golden is not shipped because every alternative was worse. It is shipped because it is the
> only ranking whose current benefits and risks are verified without relying on unresolved
> human assumptions.

## Research arc (uncertainty reduction, not metric chasing)

```text
Golden → Competitor audit → Learned-model & Cross-Encoder experiments → Rank-space Fusion
  → Judge-dependence & influence audits → Evidence-channel experiments
  → Integrity-constrained Fusion → Ω decision framework
  → Ψ candidate-specific human instrument → Φ public hiring-norms study → Ship Golden
```
Every stage **reduced uncertainty** about what is real; not every stage improved a metric.
Most alternatives are *measured negatives* — built, measured against independent labels, and
rejected on the evidence (`docs/measured_negatives.md`).

## Dashboard preview

`streamlit run omega_decision_dashboard.py` shows, in 30–60 seconds: a `NO_RANKING_DOMINATES`
decision banner · shipping-gate battery · minimax-regret frontier (with a **simulated,
model-specific** λ slider) · the 52-anomaly reconciliation + filterable table · candidate
integrity audit cards · fusion autopsy · Ψ frozen-panel status (`AWAITING HUMAN DATA`) · Φ
real-discourse findings · the complete experiment timeline · and why golden ships. It reads
only committed local artifacts; missing artifacts render "Artifact unavailable", never invented
values.

## Documentation map

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
