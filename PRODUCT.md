# HireFit — the recruiter product, not just a ranker

*A decision-support layer for Redrob: a recruiter pastes a role, gets a ranked, explained, and
integrity-screened shortlist they can act on and export — deterministic, CPU-only, and battle-proof.*

This document is the **product** view. For the ML/methodology view see `METHODOLOGY.md`; for the
shipping/reproduction view see `docs/REPRODUCTION.md`.

## The recruiter journey (what the live demo actually does)
Live now: [HuggingFace Space](https://huggingface.co/spaces/bansal1234/Hirefit) ·
[Render app](https://redrob-hirefit-ranker.onrender.com) · `streamlit run omega_decision_dashboard.py`.

1. **Bring candidates.** Upload a candidate pool (`.jsonl`/`.json`). The *real* BM25 + 33-feature
   scorer runs in-browser — CPU-only, offline, deterministic. No precomputed results, no LLM calls.
2. **Get a banded shortlist.** Candidates land in T1 (top) / T2 (shortlist) / T3 (long tail), each
   with a fit score and a one-line, **grounded** reason drawn from real profile facts.
3. **Inspect any candidate.** An explainable fit breakdown — which skills, production evidence,
   seniority, and JD signals moved the score, and which guardrail penalties fired.
4. **See the integrity call.** Every candidate carries a decision-support flag (below).
5. **Act and export.** Filter/search the shortlist; download the ranked CSV for your ATS.

## The differentiator: responsible integrity decision-support
The dataset plants ~80 "honeypot" profiles (impossible tenure — e.g. 8 years of a 3-year-old tech).
Most rankers either miss them or silently bury them. HireFit makes the call **visible and bounded**,
using a two-axis, recruiter-validated mapping (`dashboard/integrity_cards.py`):

| What we detect | Recommended action |
|---|---|
| Clean evidence | **CONTINUE** |
| Ambiguous signal | **CLARIFY** |
| Probable contradiction (e.g. tenure > tech age) | **VERIFY** — flag for human review |
| Confirmed contradiction | **BLOCK** |

Crucially it is **assistive, not automated rejection**: a flag means *"a human should look"*, never
*"this person is a fraud."* The code literally forbids claims like "confirmed fraud" / "is a honeypot."
This is why the **V6 release** keeps multiplicative integrity gates around its frontier-v5 ranking
core: it excludes every detected hard trap from the top 100 instead of letting keyword strength buy
rank. An independent recruiter's labels support that choice (`docs/external_recruiter_validation.md`).
**Our top-100 ships 0 honeypots.**

## Why this fits Redrob
- **Recruiter trust:** grounded reasons + an explicit "where to look" flag → a tool a recruiter can
  defend to a hiring manager, not a black box.
- **Production-shaped:** deterministic, CPU-only, **136.0 s for 100K on 2 CPUs**, offline — scales to a 200K pool
  without a per-candidate LLM bill. The cost-quality tradeoff is the point.
- **Auditable & fair:** counterfactual fairness tests, no candidate-ID tuning in the ranking path,
  every KPI generated from a single drift-checked manifest.
- **Public-field proof:** #1 / 673 broad mean7, #1 / 100 strongest-union mean15, and #3 / 322
  equal four-axis balance; no measured public artifact dominates all four axes.
- **Failure-safe:** exact input/model/output hashes, deterministic environment checks, and OOM-safe
  atomic publication protect a known-good shortlist.

## Honest limits / roadmap (Redrob-OS direction)
- Today it is a **resume-ranking + integrity** surface for one JD. The Redrob-OS breadth —
  natural-language people search, job/company search, multilingual (Indic) profiles, CRM/ATS sync —
  is roadmap, not shipped. The architecture (deterministic scorer + explainable features + integrity
  layer) is the right substrate for it.
- All ranking-quality numbers are dev proxies; our own frozen human lockbox is still awaiting reviewers
  (the external recruiter cross-check is the best real signal we have, and it supports the ship).

Challenge positioning and the transparent mission-derived 93.7/100 scorecard are in
`docs/CHALLENGE_POSITIONING.md`; they are not official judging weights or an official result.
