# Study Φ — Codebook v1 (frozen for the pilot)

Each opinion unit (one distinct hiring judgment) receives codes A–F. Single-coder pilot;
a second human coder + adjudication is required before the codebook is finalised for the
full corpus.

## A. Integrity stance
- `INTEGRITY_ABSOLUTE` — any intentional dishonesty ⇒ rejection.
- `INTEGRITY_HIGH` — major contradictions ⇒ rejection; minor errors may be clarified.
- `VERIFY_FIRST` — pause and verify before accept/reject.
- `CONTEXT_DEPENDENT` — depends on severity, evidence, explanation.
- `QUALITY_FIRST` — career capability outweighs non-material inconsistencies.
- `UNKNOWN` — no actionable stance (→ exclude).

## B. Inconsistency type
`minor_formatting_error · month_or_date_mismatch · employment_overlap · unexplained_gap ·
inflated_title · inflated_responsibility · inflated_skill_duration · technology_anachronism ·
fabricated_employment · fabricated_qualification · unsupported_project_claim ·
identity_or_proxy_candidate_fraud · none`

## C. Recommended action
`ignore · lower_confidence · ask_for_explanation · technical_verification · reference_check ·
background_check · continue_interview · conditional_offer · reject · blacklist_or_escalate`

## D. Severity (objective, of the inconsistency discussed)
`0 harmless · 1 minor ambiguity · 2 concerning but explainable · 3 likely material deception ·
4 decisive impossibility or fabrication`

## E. Compensating evidence cited
`technical_interview · work_sample · github_or_portfolio · references · verified_assessment ·
career_description · candidate_disclosure · consistent_external_history · none`

## F. Context
`author_claimed_role` (self_claimed) · `geography` · `startup_or_enterprise` ·
`technical_or_nontechnical_role` · `candidate_seniority` · `firsthand_or_secondhand` ·
`conditional_reasoning` (yes/no — does the opinion explicitly condition on severity/role/
explanation/"depends"/"ask them"/"could be a typo"/"pattern vs one"?)

## Coding rules
- Code the *stated* hiring judgment, not the commenter's tone.
- `conditional_reasoning=yes` whenever the unit hinges the decision on a contingency.
- If the author claims a role, record it but mark confidence `self_claimed`.
- Truncated excerpts: code only what is visible; flag `notes=truncated` if uncertain.
