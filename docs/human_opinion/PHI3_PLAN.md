# Φ-3 — Human-completed validation (plan; NOT executed by automation)

This branch (`research/phi3-human-validation`) holds the work that **only real humans can
complete**. The frozen pilot (`06bca55`) and Φ-2 continuation are preserved unchanged. **No
algorithm may substitute for the steps below** — doing so (simulated reviewers, self-coded
"second" passes, weak-source corpus padding) would manufacture false confidence, which this
project refuses. Automated corpus expansion is **ended**.

## Continuation 1 — Independent second coder (highest immediate value; instrument ready)
Everything needed already exists and is frozen:
- `codebook_v2.md` (two-axis definitions) + `codebook_v1.md`.
- `second_coder_packet.jsonl` — de-identified, **no coder-1 labels**, no aggregate findings,
  no golden/fusion/Ω context, no preferred conclusion.
- `phi2_kappa.py` — computes agreement **separately** for inclusion, evidence_status,
  hiring_action, severity (quadratic-weighted), red_flag_type; prints `AWAITING_SECOND_CODER`.

Procedure: give a genuinely independent coder 5–8 **training examples not in the corpus**;
discuss codebook interpretation only; freeze clarifications; then code the full packet blind.
Drop their labels into `second_coder_responses.jsonl` and run `phi2_kappa.py`. Report κ per
axis — do **not** collapse to one number. The decision-critical disagreement to watch is the
boundary between **PROBABLE_CONTRADICTION × VERIFY** and **CONFIRMED_CONTRADICTION × BLOCK**.

## Continuation 2 — Real recruiter & India-specific perspectives (Φ-3 proper)
Legitimate, targeted collection only (no bulk scraping; respect platform ToS + attribution):
- 5–10 recruiters / HR / background-verification professionals code a small public-discourse
  subset, or short structured interviews on **generic** scenarios (kept separate from Ψ).
- Indian hiring managers on relieving-date, overlapping/dual employment, PF/UAN, and
  experience-letter discrepancies.
- Neutral surveys only where permitted; public professional posts only where reuse/attribution
  are appropriate. Hash identifiers; short excerpts; no model training on content.
Keep as a **separate source composition** (new manifest + hash); the SE units remain the
*HR/workplace-process* stratum, never relabeled "recruiter" without verified author roles.

## Continuation 3 — Already shipped (product feature, golden untouched)
The non-ranking integrity audit card (`experiments/integrity_card.py`,
`integrity_cards_demo.md`) is built and operates downstream of the frozen ranking. No human
input required; included here only as the cross-reference.

## Completion gates (publication-quality) — all require humans
Recruiter + India strata populated · ≥1 independent second coder completes the frozen sample ·
anachronism cell reaches qualitative saturation · thread-level & source-stratum sensitivity
reported · contrary evidence preserved · conclusion survives removing the largest threads ·
report states prevalence cannot be estimated from the corpus.

## Standing claim (unchanged)
Public hiring discourse supports a severity- and evidence-conditioned, verification-first
workflow — not a universal integrity penalty — justifying a multi-state integrity interface,
but it does **not** determine the Redrob ranking. The frozen Ψ panel remains the sole
candidate-specific instrument; golden (`af8f2b32`) remains the production baseline and one-command
fallback, while the validated severity-gated Copeland hedge (`24f84f4b`) is the shipped submission.
