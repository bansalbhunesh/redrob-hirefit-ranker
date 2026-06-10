# Honeypot Audit (Phase 1.4)

## Ambiguity rubric (committed BEFORE reviewing any flagged profile)

A hard honeypot flag is **ambiguous** if a plausible *honest data-entry*
explanation exists for the triggering condition. Concretely, per flag class:

| Flag class | Fires when | Ambiguous if |
|---|---|---|
| `experience_timeline_exceeds_claim` | sum(career duration_months) > claimed YoE*12 + 30 | overlapping roles could honestly explain the overshoot: 2+ jobs whose date ranges overlap (moonlighting, part-time + full-time, advisor roles held concurrently), or a current role plus consulting listed in parallel |
| `career_history_too_short_for_claimed_yoe` | YoE >= 5 and history < 45% of claim | the profile shows clear signs of an abbreviated history (e.g., only the most recent 1-2 roles listed, education end-year consistent with the claimed YoE) |
| `expert_skill_zero_duration` | >=2 core or >=5 any "expert" skills with 0 months | the zero-duration expert skills look like a freshly imported/auto-synced skill list: several skills added with uniform zero duration AND nonzero endorsements or matching career evidence elsewhere in the profile |
| `multiple_current_jobs` | >2 roles marked is_current | the "current" roles are plausibly concurrent by nature (advisor, open-source maintainer, part-time lecturer alongside a primary job) |
| `impossible_education_timeline` | end_year < start_year, or years outside 1970-2035 | a single transposed pair (e.g., 2019-2015) where every other date on the profile is coherent — a typo, not a fabricated career |
| `title_description_contradiction` | non-target title (e.g., "Marketing Manager") + IR/ranking-heavy descriptions | the title is plausibly stale or generalist (e.g., "Operations Manager" at a tiny startup actually doing technical work corroborated by skills/education) |

Default stance: a flag is **upheld** (genuine honeypot) when the violation is
large, repeated, or co-occurs with other flags; honest-explanation findings
must cite the specific fields that support the explanation. The reviewer must
not look at metric impact while classifying (classification first, scoring
after).

Pre-registered remediation: if ANY flagged profile in a class is judged
ambiguous, soften that class's multiplier from hard 0.0 to 0.05 (class-level,
not global), re-rank, re-validate, and update the golden hash citing this
audit. If none are ambiguous, hard-zero stands.

## Flagged population

Hard honeypots (multiplier 0.0): **53** (full records: `artifacts/honeypot_flagged.jsonl`).

| flag class | count |
|---|---|
| `career_history_too_short_for_claimed_yoe` | 23 |
| `experience_timeline_exceeds_claim` | 22 |
| `expert_skill_zero_duration` | 8 |

Candidates with 2+ hard flags: **0** of 53.

## Near-miss false-negative check

20 closest near-misses (exactly one condition almost met) in `artifacts/honeypot_nearmiss.jsonl`:

| candidate_id | near class | closeness | detail |
|---|---|---|---|
| CAND_0055792 | `expert_skill_zero_duration` | 1.00 | 1 core expert-zero skill (fires at 2) |
| CAND_0065096 | `expert_skill_zero_duration` | 1.00 | 1 core expert-zero skill (fires at 2) |
| CAND_0095140 | `expert_skill_zero_duration` | 1.00 | 1 core expert-zero skill (fires at 2) |
| CAND_0033817 | `expert_skill_zero_duration` | 0.90 | 4 expert-zero skills (fires at 5) |
| CAND_0046689 | `expert_skill_zero_duration` | 0.90 | 4 expert-zero skills (fires at 5) |
| CAND_0072379 | `expert_skill_zero_duration` | 0.90 | 4 expert-zero skills (fires at 5) |
| CAND_0095480 | `expert_skill_zero_duration` | 0.90 | 4 expert-zero skills (fires at 5) |
| CAND_0010770 | `career_history_too_short_for_claimed_yoe` | 0.77 | history ratio 0.47 (fires below 0.45) |
| CAND_0001610 | `experience_timeline_exceeds_claim` | 0.58 | career 61m vs claim 36m (+30 grace); 5m under threshold |
| CAND_0039754 | `career_history_too_short_for_claimed_yoe` | 0.45 | history ratio 0.51 (fires below 0.45) |
| CAND_0039521 | `experience_timeline_exceeds_claim` | 0.42 | career 59m vs claim 36m (+30 grace); 7m under threshold |

## Verdicts

_(per-candidate verdict table; manual verification pass pending user review)_
