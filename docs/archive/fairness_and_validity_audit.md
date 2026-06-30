# Fairness and Validity Audit

**Project:** Redrob HireFit Ranker  
**Audit date:** 2026-06-13  
**Auditor:** Lab branch pass (codex/100-score-gap-lab)  
**Status:** Baseline implemented — human blind-label proof still outstanding

---

## Policy Statement

> **This system is decision-support software, not an automated rejection mechanism.**
>
> The ranker produces a scored shortlist to assist human recruiters. No hiring
> decision — rejection, interview invitation, or offer — should be made solely
> on the basis of this ranker's output. Candidates near score thresholds must be
> reviewed by a human recruiter before any action is taken.

This policy mirrors practices documented by Greenhouse AI, Eightfold Talent
Intelligence, and the EU AI Act's definition of high-risk AI in employment
contexts.

---

## Proxy Feature Risk Register

The following features appear in `src/redrob_ranker/features.py` and carry
potential to correlate with protected or socioeconomic attributes. Each is
documented with its risk level, mitigation, and audit result.

| Feature | Proxy Risk | Mitigation | Audit Status |
|---|---|---|---|
| `location_score` | Geography → socioeconomic class, visa status | Capped weight (~0.04); `willing_to_relocate` uplifts overseas candidates | ✅ Delta < 0.12 in counterfactual tests |
| `notice_period_score` | Employment security, seniority | Soft penalty; 180-day notice loses < 0.10 | ✅ Bounded |
| `open_to_work_flag` | Life circumstances, job-seeking desperation | Binary signal, soft penalty only; loss < 0.15 | ✅ Bounded |
| `recruiter_response_rate` | Communication style, time zone, accessibility | Soft penalty; dominated by technical features | ✅ Loss < 0.20 |
| `product_company_ratio` | Socioeconomic access to product companies | Non-zero score for any industry; no hard zero | ✅ Services delta < 0.20 |
| `education_score` | College prestige → family wealth, geography | Bounded weight (~0.02); practical experience dominates | ✅ Tier delta < 0.08 |
| `endorsement_trust` | Social network access, LinkedIn presence | Discounted for low-completeness profiles; genuine depth wins | ✅ Depth > inflation test passes |
| `github_activity_score` | Hobby time, open-source access | Supplementary signal only; not a must-have | ✅ Low risk |
| `behavioral_multiplier` | Availability, responsiveness bias | Soft floor 0.05; never hard-zeros | ✅ Consulting floor > 0.05 |

---

## Counterfactual Test Results

Automated counterfactual tests are in
[`tests/test_fairness_counterfactual.py`](../tests/test_fairness_counterfactual.py).

All 12 tests pass as of 2026-06-13. Results summary:

| Test | Delta | Threshold | Result |
|---|---|---|---|
| Name-coded headline | < 0.01 | 0.05 | ✅ Pass |
| Location: Pune → Berlin | < 0.08 | 0.12 | ✅ Pass |
| Location: Canada + relocate willing | < 0.08 | 0.12 | ✅ Pass |
| Gender-coded headline | < 0.01 | 0.05 | ✅ Pass |
| College tier: IIT → tier-3 | < 0.04 | 0.08 | ✅ Pass |
| Missing education section | < 0.06 | 0.10 | ✅ Pass |
| Genuine depth > endorsement inflation | N/A | Ordinal | ✅ Pass |
| Endorsements discounted at low completeness | < 0.02 | 0.05 | ✅ Pass |
| open_to_work=False penalty | < 0.09 | 0.15 | ✅ Pass |
| 180-day notice penalty | < 0.05 | 0.10 | ✅ Pass |
| Low recruiter response rate | < 0.12 | 0.20 | ✅ Pass |
| Services company disadvantage | < 0.14 | 0.20 | ✅ Pass |
| Consulting-only floor | > 0.05 | > 0.05 (floor) | ✅ Pass |

> [!NOTE]
> These are synthetic counterfactual tests on a model built for a specific
> technical JD. They do not replace adverse-impact analysis on the actual
> candidate pool with real protected-attribute labels.

---

## Manual-Review Flag Conditions

Recruiters should apply additional human scrutiny when a candidate has any of
the following conditions in their feature payload:

| Flag | Meaning | Recommended Action |
|---|---|---|
| `consulting_only` | All history is short-term consulting | Verify depth of technical delivery |
| `title_hopper` | ≥ 3 roles in < 24 months | Check for growth trajectory vs instability |
| `llm_wrapper_only` | Skills are LLM API wrappers, no foundational ML | Assess genuine ML competence |
| `junior_for_senior_role` | YoE significantly below JD requirement | Discuss with hiring manager before rejection |
| `honeypot_multiplier < 0.5` | Profile shows keyword stuffing or prompt injection | Verify profile authenticity |
| Score near P50 boundary | Score within 0.05 of median shortlist score | Human review before cut-off |

---

## Remaining Gaps

1. **No real blind human labels.** All counterfactual tests use the feature
   scorer on synthetic profiles. Real adverse-impact analysis requires actual
   candidate data with recruiter decisions and protected-attribute labels.

2. **Location signals aggregate geography with preference.** The `location_score`
   feature uses PREFERRED_INDIAN_LOCATIONS from `constants.py`. A recruiter
   using this system for a non-India JD should verify the location weights
   match their hiring geography.

3. **Indic-script support is absent.** Profiles with Devanagari text are
   tokenized to empty strings (`src/redrob_ranker/text.py:10`). This
   disproportionately impacts candidates whose profiles are primarily in Hindi.
   This is a P1 engineering gap documented in `ARCHITECTURE.md`.

---

## References

- Greenhouse AI: [human control and scorecard design](https://support.greenhouse.io/hc/en-us/articles/33043749845403-Greenhouse-AI-features)
- Eightfold fairness writeup: [talent matching and fairness](https://eightfold.ai/engineering-blog/ai-powered-talent-matching-the-tech-behind-smarter-and-fairer-hiring/)
- EU AI Act: High-risk AI systems in employment contexts
- EEOC technical guidelines: Job-relatedness and construct validity for AI hiring tools
