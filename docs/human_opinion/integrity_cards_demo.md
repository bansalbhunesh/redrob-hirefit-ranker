# Integrity Audit Cards — demo (downstream of frozen golden; ranking unchanged)

Replaces `honeypot=true/false` with a proportionate two-axis state validated by Study Φ.
Golden (`af8f2b32`) and all scores are byte-identical; this is an annotation layer only.

Distribution over golden's top-100: PROBABLE_CONTRADICTION->VERIFY:52, CLEAR->CONTINUE:45, AMBIGUOUS->CLARIFY:3

## CAND_0081846
- Role fit: **0.838**
- Evidence status: **CLEAR**
- Recommended action: **CONTINUE**
- Reason: No meaningful contradictory evidence detected.
- Corroborating evidence: production/retrieval career evidence, verified assessment, ranking/IR experience
- Verification request: None required.

## CAND_0065195
- Role fit: **0.584**
- Evidence status: **PROBABLE_CONTRADICTION**
- Recommended action: **VERIFY**
- Reason: Claimed tenure in 'QLoRA' is 93 months, which exceeds the technology's plausible age (~48 months).
- Corroborating evidence: verified assessment
- Verification request: Ask the candidate for the project timeline and version history of their QLoRA work.

## CAND_0077337
- Role fit: **0.828**
- Evidence status: **AMBIGUOUS**
- Recommended action: **CLARIFY**
- Reason: Incomplete or borderline résumé metadata (e.g. abbreviated history vs claimed experience, or uncorroborated expert skill) with a plausible innocent explanation.
- Corroborating evidence: production/retrieval career evidence, verified assessment, ranking/IR experience
- Verification request: Ask the candidate to fill in missing dates/durations; corroborate in interview.
