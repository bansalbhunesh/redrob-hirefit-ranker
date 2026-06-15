# Honeypot Detector Consensus — why competitor flag-counts are not evidence

## The plausibility test the field fails

The official challenge plants **~80** honeypots in 100 000 candidates (0.08%). A detector
that *targets the planted traps* should flag a number of that order — tens to low hundreds,
each backed by a concrete contradiction. Counts reported for competitor detectors in the
audit material:

| detector | flagged | % of pool | plausible as "the ~80 planted traps"? |
|---|---|---|---|
| our hard detector | **294** | **0.29%** | yes — right order of magnitude, derived per-candidate |
| calibrated peers | ~53–80 | ~0.05–0.08% | yes |
| aggressive repo A | 7 580 | 7.6% | **no** — flags 95× the planted count |
| aggressive repo B | 16 157 | 16% | **no** |
| aggressive repo C | 55 942 | 56% | **no** — flags the majority of the dataset |

A detector that flags 7–56% of *everyone* is measuring **generic low quality / weak profiles
/ keyword anomalies**, not the planted honeypots. Its large count is a liability (it discards
real candidates), not a sign of superior trap detection. **Flag-count is not a quality
metric;** precision against decidable contradictions is.

## What a *defensible* honeypot flag looks like

Every flag we raise is **derived from contradictory fields**, not a hard-coded ID list:

- `tech_anachronism` — a skill/job claims a technology for longer than (or before) it has
  existed (e.g., "RAG, 94 months" when RAG is ~3 years old). Severity from the gap.
- `experience_timeline_exceeds_claim` — summed career months exceed the claimed YoE window.
- `impossible_education_timeline` — end-year < start-year, or years out of range.
- `multiple_current_jobs` — more than two concurrently-current positions.
- `expert_skill_zero_duration` (uncorroborated) — expert proficiency, zero months, and the
  skill appears nowhere in career text or assessments.

Each is reproducible, explainable to a human reviewer field-by-field, and **falsifiable**.
The 294 we flag are exactly these; we do not pad the count with low-quality profiles.

## Two-level discipline (see `constrained_rank_fusion_study.md`)

Crucially we then **split** these into HARD (decisive impossibility — never rescued by
relevance) and AMBIGUOUS (innocent-import reading exists — rescue-eligible with multi-channel
evidence). The aggressive competitor detectors collapse this distinction, which is how they
reach 16–56%: they treat "abbreviated history" or "missing skill duration" as a trap. Those
are data-quality warnings, not impossibilities.

## Cross-repository consensus (method; competitor code not executed)

A full consensus matrix requires running each repo's detector on the same 100K pool. We do
**not** execute competitor code (untrusted code + offline/disk constraints), so the matrix is
specified but not populated here. The defensible claims that do **not** require it — and that
this report makes — are: (1) any detector flagging ≥1% of the pool is not isolating the ~80
planted traps; (2) our 0.29% rate, derived from per-candidate temporal contradictions, is the
calibrated reference; (3) flag-count must never be cited as detection quality. Whether a
repo's *own* submitted top-100 contains its *own* flagged candidates is the one consistency
check worth running per-repo if their flag sets are ever published.
