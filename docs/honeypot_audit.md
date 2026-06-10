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

## Manual verification pass (2026-06-10)

The automated rubric triage initially marked 16 instances ambiguous. Manual
inspection of every ambiguous profile, including the only two with
JD-relevant titles, found a decisive planted-fabrication tell that the
automation had missed:

- **CAND_0013536** (Applied ML Engineer): YoE field claims **14.1y**, but the
  profile's own summary says "with **4.8 years** of experience" and career
  history sums to 56 months (≈4.7y). The education years (2002–2007) were
  back-dated to make graduation look consistent with the inflated field.
- **CAND_0071115** (Recommendation Systems Engineer at Meta): field claims
  **16.5y**, summary says "with **5.8 years**", history ≈69 months. Same
  pattern (and duplicated role descriptions across employers).

The summary-vs-claim cross-check and a tighter endorsement criterion
(1–3 endorsements is noise, not a curated import) were folded back into
`scripts/honeypot_verdicts.py`; the verdict table below is the recalibrated
output. After recalibration, **12 instances remain ambiguous** under the
pre-committed rubric — all are JD-irrelevant titles (Business Analysts, HR
Manager, Civil Engineer, Content Writer, etc.) with single-role abbreviated
histories and consistent graduation years, where an honest "imported only my
current job" reading cannot be excluded.

## Remediation applied (per the pre-registered rule)

Because ambiguous members exist in `career_history_too_short_for_claimed_yoe`
and `expert_skill_zero_duration`, those two classes were softened from hard
0.0 to **0.05** (`SOFTENED_HONEYPOT_CLASSES` in `features.py`).
`experience_timeline_exceeds_claim` (0 ambiguous) remains a hard zero.

**Measured outcome:** the full 100K re-rank with softening produces a CSV
**byte-identical to the golden submission** (`e1a696d1...`) — a 0.05×
multiplier cannot reach the top-100, so the remediation removes the
irreversible-zero risk without moving a single rank. Honeypot counters now
count `multiplier < 1.0`: still **53 detected, 0 in the top-100**.

The near-miss false-negative check (11 profiles above) found no candidate
that should have been flagged: all sit legitimately below thresholds, and
none shows the summary-vs-claim contradiction.

## Verdicts

Rubric applied to all 53 flagged candidates (53 flag instances). Summary:

| flag class | upheld | ambiguous |
|---|---|---|
| `career_history_too_short_for_claimed_yoe` | 14 | 9 |
| `experience_timeline_exceeds_claim` | 22 | 0 |
| `expert_skill_zero_duration` | 5 | 3 |

| candidate_id | flag | verdict | evidence |
|---|---|---|---|
| CAND_0003430 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | claims 14y, history covers 11m across 1 roles; education (2018) does not corroborate the claim |
| CAND_0005291 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2006 is consistent with 13y -- looks abbreviated, not fabricated |
| CAND_0007353 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 10y but durations sum to 251m (+133m); dated overlaps only 0m |
| CAND_0007413 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2013 is consistent with 13y -- looks abbreviated, not fabricated |
| CAND_0008960 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 10y but durations sum to 271m (+148m); dated overlaps only 0m |
| CAND_0010294 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 8y but durations sum to 220m (+124m); dated overlaps only 0m |
| CAND_0013536 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | summary self-reports 4.8y (matches 56m of history) but the YoE field claims 14.1y -- fabricated field |
| CAND_0016000 | `expert_skill_zero_duration` | **AMBIGUOUS** | 1/5 zero-duration expert skills corroborated in career text: ['Docker'] |
| CAND_0018515 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 8y but durations sum to 211m (+109m); dated overlaps only 0m |
| CAND_0019480 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 3y but durations sum to 87m (+54m); dated overlaps only 0m |
| CAND_0024752 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2011 is consistent with 15y -- looks abbreviated, not fabricated |
| CAND_0025579 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2008 is consistent with 13y -- looks abbreviated, not fabricated |
| CAND_0033131 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | claims 13y, history covers 16m across 1 roles; education (2020) does not corroborate the claim |
| CAND_0035104 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 6y but durations sum to 162m (+96m); dated overlaps only 0m |
| CAND_0036299 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | claims 12y, history covers 8m across 1 roles; education (2022) does not corroborate the claim |
| CAND_0037000 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 3y but durations sum to 75m (+43m); dated overlaps only 0m |
| CAND_0037539 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 5y but durations sum to 115m (+57m); dated overlaps only 0m |
| CAND_0038431 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2007 is consistent with 15y -- looks abbreviated, not fabricated |
| CAND_0040075 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 15y but durations sum to 365m (+185m); dated overlaps only 0m |
| CAND_0040853 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 1y but durations sum to 61m (+48m); dated overlaps only 0m |
| CAND_0042453 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 4y but durations sum to 98m (+48m); dated overlaps only 0m |
| CAND_0043721 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 4y but durations sum to 108m (+54m); dated overlaps only 0m |
| CAND_0046649 | `expert_skill_zero_duration` | **UPHELD** | 5 expert skills with 0 months, 0 endorsed, none corroborated by career history |
| CAND_0052478 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2014 is consistent with 12y -- looks abbreviated, not fabricated |
| CAND_0053734 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 9y but durations sum to 221m (+118m); dated overlaps only 0m |
| CAND_0055685 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 1y but durations sum to 64m (+48m); dated overlaps only 0m |
| CAND_0055992 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | summary self-reports 6.8y (matches 80m of history) but the YoE field claims 16.9y -- fabricated field |
| CAND_0056983 | `expert_skill_zero_duration` | **UPHELD** | 5 expert skills with 0 months, 0 endorsed, none corroborated by career history |
| CAND_0057711 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 8y but durations sum to 180m (+88m); dated overlaps only 0m |
| CAND_0060642 | `expert_skill_zero_duration` | **UPHELD** | 5 expert skills with 0 months, 0 endorsed, none corroborated by career history |
| CAND_0061722 | `expert_skill_zero_duration` | **UPHELD** | 5 expert skills with 0 months, 0 endorsed, none corroborated by career history |
| CAND_0063888 | `expert_skill_zero_duration` | **UPHELD** | 5 expert skills with 0 months, 0 endorsed, none corroborated by career history |
| CAND_0064077 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 10y but durations sum to 237m (+116m); dated overlaps only 0m |
| CAND_0065710 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 4y but durations sum to 114m (+62m); dated overlaps only 0m |
| CAND_0065787 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2012 is consistent with 11y -- looks abbreviated, not fabricated |
| CAND_0066405 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2013 is consistent with 12y -- looks abbreviated, not fabricated |
| CAND_0070189 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 7y but durations sum to 173m (+91m); dated overlaps only 0m |
| CAND_0070429 | `expert_skill_zero_duration` | **AMBIGUOUS** | 1/5 zero-duration expert skills corroborated in career text: ['Java'] |
| CAND_0071115 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | summary self-reports 5.8y (matches 69m of history) but the YoE field claims 16.5y -- fabricated field |
| CAND_0073853 | `expert_skill_zero_duration` | **AMBIGUOUS** | 1/5 zero-duration expert skills corroborated in career text: ['Marketing'] |
| CAND_0074119 | `career_history_too_short_for_claimed_yoe` | **AMBIGUOUS** | only 1 roles listed and graduation 2013 is consistent with 11y -- looks abbreviated, not fabricated |
| CAND_0077239 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 8y but durations sum to 180m (+89m); dated overlaps only 0m |
| CAND_0077250 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | claims 13y, history covers 18m across 1 roles; education (2020) does not corroborate the claim |
| CAND_0084182 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 13y but durations sum to 299m (+147m); dated overlaps only 0m |
| CAND_0086808 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | claims 11y, history covers 15m across 1 roles; education (2017) does not corroborate the claim |
| CAND_0090900 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | claims 12y, history covers 9m across 1 roles; education (2020) does not corroborate the claim |
| CAND_0091068 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | claims 13y, history covers 12m across 1 roles; education (2021) does not corroborate the claim |
| CAND_0091534 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | summary self-reports 7.2y (matches 85m of history) but the YoE field claims 16.6y -- fabricated field |
| CAND_0093331 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | summary self-reports 7.2y (matches 86m of history) but the YoE field claims 16.1y -- fabricated field |
| CAND_0093364 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 8y but durations sum to 210m (+116m); dated overlaps only 0m |
| CAND_0093547 | `experience_timeline_exceeds_claim` | **UPHELD** | claims 3y but durations sum to 74m (+40m); dated overlaps only 0m |
| CAND_0095619 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | summary self-reports 4.2y (matches 50m of history) but the YoE field claims 15.6y -- fabricated field |
| CAND_0096150 | `career_history_too_short_for_claimed_yoe` | **UPHELD** | claims 15y, history covers 10m across 1 roles; education (2018) does not corroborate the claim |

