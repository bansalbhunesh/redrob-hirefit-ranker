# Integrity Decision Atlas — Study Φ (HN pilot surface)

The deliverable that matters more than a single "integrity-first %": a **severity-conditioned
decision surface**. Derived from the single-coder HN pilot (n = 19); **directional, not
representative**. Recruiter / India / multi-coder strata are required to harden it.

## Severity × recommended action (observed in the pilot)

| objective severity | dominant recommended action(s) | reading |
|---|---|---|
| 0 — harmless | continue_interview, work_sample, ignore | judge by demonstrated capability |
| 1 — minor ambiguity | ignore (mostly); rare strict reject | usually tolerated; one outlier rejects |
| 2 — concerning but explainable | background_check, technical_verification | **investigate before deciding** |
| 3 — likely material deception | background_check → reject | verify, then reject if confirmed |
| 4 — decisive impossibility / fabrication | technical_verification → reject | confirm, then exclude |

## The headline structure: it is NOT a binary

Humans (in this stratum) do **not** apply one universal penalty. They run a **verification-first,
severity-graded** policy: *ignore* trivia, *test* capability, *verify* concerning claims, and
*reject* only confirmed material fabrication. This is the empirical analogue of the product
proposal **CLEAR / CLARIFY / VERIFY / BLOCK**, and it is far more recruiter-authentic than
`honeypot = true/false`.

## Mapping to our anachronism flag (the decision-critical cell)

Our anachronism detector fires on "claimed tech tenure longer than the tech existed." In the
pilot, that class sits at **severity 0–2** in human eyes and maps to **ignore / verify**, **not
auto-reject** — engineers expect the *interview* to settle whether the person can actually do
the work. Implication for the Redrob decision: an anachronism flag is, to these humans, a
**VERIFY signal, not a BLOCK signal** — which argues against hard-excluding those candidates
purely on the date anomaly. (Caveat: engineer stratum only; recruiters may treat it as higher
severity / more BLOCK-like — exactly what the full study must measure.)

## Proposed product output (ranking stays frozen)
```
Role quality: High
Integrity status: VERIFY  (CLEAR | CLARIFY | VERIFY | BLOCK)
Reason: Claimed technology tenure predates the technology's public availability
Recommended action: Ask for project timeline; verify employment dates
```
The four-level integrity status is the recruiter-authentic replacement for the binary flag;
the ranking itself is unchanged.
