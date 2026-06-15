# Study Φ-2 — Validation continuation (HR/Workplace stratum, two-axis model, second-coder ready)

Continuation of the frozen Φ pilot (`06bca55`), preserved exactly. Φ-2 targets the two missing
sources of validity — reviewer-perspective coverage and coding reliability — using only
ToS-clean data and never faking a second coder.

## What was added (real data)
- **Workplace Stack Exchange stratum** (official API, CC-BY-SA): 6 voted-answer opinion units
  on HR/background-check policy and India dual-employment/relieving-date scenarios — the
  process/recruiter perspective HN lacks.
- **Deliberate anachronism expansion** (HN + SE): targeted queries; only ~2 new genuine hiring
  judgments surfaced — most "X years of Kubernetes/RAG" hits are *tech debates*, not hiring
  decisions. **The anachronism-decision cell is n = 5 and NOT saturated** (reported honestly,
  not padded).
- **Two-axis codebook v2** (`codebook_v2.md`): Evidence status (CLEAR / AMBIGUOUS /
  PROBABLE_CONTRADICTION / CONFIRMED_CONTRADICTION) × Hiring action (CONTINUE / CLARIFY /
  VERIFY / DOWNRANK / BLOCK). Pilot v1 codes deterministically re-mapped; combined corpus
  n = 27 (`corpus_phi2.csv`, hash `fcf324e0`).

## Two-axis surface (single-coder, n=27, NOT representative)
| evidence status | dominant action(s) |
|---|---|
| CLEAR | CONTINUE (9/9) |
| AMBIGUOUS | CONTINUE / CLARIFY (one India-overlap BLOCK) |
| PROBABLE_CONTRADICTION | **VERIFY** (6), BLOCK (2), DOWNRANK (1) |
| CONFIRMED_CONTRADICTION | VERIFY (n=1) |

Severity → action is monotone (sev0→CONTINUE, sev2→VERIFY, sev3→BLOCK/VERIFY). This confirms
the pilot's headline with a cleaner instrument: **"suspicious" (evidence) and "reject"
(action) are distinct** — most contradictions trigger VERIFY, not BLOCK.

## Stratum difference (the Φ-2 contribution)
- **Hacker News (engineers/founders):** CONTINUE-heavy (11 CONTINUE, 8 VERIFY, 2 BLOCK).
- **Workplace SE (HR/process):** CLARIFY / DOWNRANK / VERIFY / BLOCK — more procedural and
  less forgiving; the India dual-employment case is the lone clear BLOCK.

This supports the predicted recruiter-vs-engineer divergence: **process/HR discourse leans
verification-and-procedure; engineer discourse leans capability-and-continue.** Directional
(SE n=6); the full recruiter stratum still requires ToS-appropriate Reddit/LinkedIn access.

## Second-coder reliability — ready, not faked
`second_coder_packet.jsonl` is **de-identified, carries NO coder_1 labels**, no expected
conclusion. `phi2_kappa.py` computes Cohen's κ (evidence, action), quadratic-weighted κ
(severity), reported **separately per axis** (never collapsed). It currently prints
`AWAITING_SECOND_CODER`. **I did not self-code a second pass and call it IRR** — two passes by
the same system share correlated errors and would be fake reliability, the exact trap this
project refuses.

## Still frozen protocol (NOT retrieved — honest gaps)
Recruiter-Reddit and India-Reddit strata (bulk access is ToS-restricted; no model training on
content) and the full ≥120-unit, saturated, double-coded study. These are the publication-
quality completion gates, deferred to real collection with appropriate access + a human coder.

## Firewall (unchanged)
Φ-2 does not touch Ψ, Ω, golden (`af8f2b32`), or any preregistered threshold. The pilot commit
`06bca55` is preserved. A Φ-motivated Ψ change would go to `psi_v2/` with a new hash.

## Standing conclusion (unchanged, now better-instrumented)
> Public hiring discourse supports a severity- and evidence-conditioned workflow rather than a
> universal integrity penalty: minor inconsistencies are tolerated or clarified, concerning
> claims trigger verification, decisive/repeated deception trends toward rejection — and HR/
> process voices are more procedural than engineers. These norms justify a multi-state
> integrity interface (CLEAR/CLARIFY/VERIFY/BLOCK), but do not determine the ranking of the
> Redrob candidates; the frozen Ψ panel remains the sole candidate-specific instrument.
