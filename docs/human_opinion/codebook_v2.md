# Study Φ-2 — Codebook v2 (two-axis; supersedes v1's single stance for analysis)

v1 conflated "the profile looks suspicious" with "the person should be rejected." v2 splits
the judgment into two independent axes. Pilot v1 codes are deterministically re-mapped to v2
(see `phi2_code.py`) so the combined corpus is analysed on one scheme.

## Axis 1 — Evidence status (what is actually established)
- `CLEAR` — no meaningful contradictory evidence.
- `AMBIGUOUS` — incomplete / supports multiple explanations.
- `PROBABLE_CONTRADICTION` — appears inconsistent but lacks decisive verification.
- `CONFIRMED_CONTRADICTION` — objectively impossible or externally disproved.

## Axis 2 — Recommended hiring action (what to do about it)
- `CONTINUE` — no intervention needed.
- `CLARIFY` — ask the candidate for context.
- `VERIFY` — require technical / documentary / reference evidence.
- `DOWNRANK` — keep considering at reduced confidence.
- `BLOCK` — reject regardless of otherwise-strong quality.

A candidate can be `evidence=PROBABLE_CONTRADICTION` + `action=VERIFY` — never forced into a
binary honeypot label. This is the recruiter-authentic replacement for `honeypot=true/false`.

## Deterministic re-map of v1 → v2 (pilot)
- evidence_status from severity: 0→CLEAR · 1→AMBIGUOUS · 2/3→PROBABLE_CONTRADICTION · 4→CONFIRMED_CONTRADICTION
- hiring_action from v1 action: ignore/continue_interview/work_sample→CONTINUE · lower_confidence→DOWNRANK ·
  ask_for_explanation→CLARIFY · technical_verification/background_check/reference_check→VERIFY · reject/blacklist→BLOCK

Retained from v1: inconsistency type, severity (0–4), compensating evidence, context
(role self_claimed, geography, seniority, firsthand), conditional_reasoning. Single-coder;
a second human coder + κ (per `phi2_kappa.py`) is required before any publishable claim.
