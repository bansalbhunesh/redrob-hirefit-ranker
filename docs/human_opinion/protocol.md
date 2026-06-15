# Study Φ — Public Hiring Norms Atlas: PROTOCOL (frozen)

**Purpose (not candidate ranking):** discover the human decision *rules* around résumé
integrity — when do hiring professionals ignore, lower confidence, ask for clarification,
verify, or reject? Φ is **external qualitative triangulation** for Ω's utility-worlds. It
**cannot** rank the Redrob candidates or set λ; only the frozen blinded Ψ panel does that.

**Separation (hard rule):** Φ must not modify Ψ's questions, thresholds, sampling, or
shipping gates. If Φ ever motivates a change, create `psi_v2/` with a new manifest+hash and
preserve the original Ψ unchanged.

## Frozen research questions
Primary: when strong career evidence conflicts with résumé-integrity concerns, what action
do real hiring professionals recommend? Secondary (frozen): mistakes vs deception; which
inconsistencies trigger auto-reject vs clarification; can projects/technical evidence
compensate for questionable dates; does seniority change it; recruiters vs engineers;
startup vs enterprise; pre- vs post-AI discourse; what evidence restores trust; is
integrity-first-vs-quality-first a false binary (verification-first)?

## Source strata (full study)
Hacker News (founders/senior eng/hiring mgrs) · recruiter Reddit · engineering Reddit ·
Workplace StackExchange · engineering hiring blogs · recruiter/LinkedIn commentary ·
India-specific hiring discussions. **This pilot covers only the Hacker News stratum** (the
ToS-clean public API). Other strata require ToS-appropriate access + a second human coder
and are deferred to the full study.

## Sampling
Full study: 120–180 unique opinion units; coverage quotas per source/stance/time (NOT
prevalence estimates); time strata pre-2023 / 2023–2024 / 2025–2026. **Unit = one distinct
hiring judgment** (retain `thread_id`; report comment-level AND thread-level, the latter more
conservative). Engagement/upvotes = visibility metadata ONLY, never counted as votes.

## Inclusion / exclusion (frozen)
Include: clear hiring recommendation about résumé truth/dates/experience/evidence with
explained reasoning, sufficient context, publicly accessible. Exclude: generic formatting /
ATS advice; no decision/reasoning; jokes/ragebait; duplicate; unrelated criminal fraud; media
summary with no practitioner position; "will they get caught?" only. Every exclusion is
logged with a reason (`exclusion_log.csv`).

## Coding & quality (full study)
Codebook v1 (`codebook_v1.md`): integrity stance · inconsistency type · severity (0–4) ·
recommended action · compensating evidence · context (author self-claimed role, geography,
seniority, startup/enterprise, firsthand). 20-item pilot → refine codebook → freeze v1 →
double-code ≥30% with a SECOND human coder → adjudicate → preserve all codes + disagreements
+ reflexivity log. **This pilot is single-coder** (only one coder available); intercoder
reliability is therefore NOT established and is required before any publishable claim.

## Limits (binding)
No representativeness/prevalence claims; corpus is platform- and algorithm-shaped; author
roles are `self_claimed`; short excerpts only; hashed authors; **no model training on the
content**. Φ establishes the *structure* of the integrity↔quality trade-off; Ψ remains the
sole candidate-specific confirmatory instrument.
