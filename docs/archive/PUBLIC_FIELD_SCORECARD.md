# Public-field scorecard

> Honesty note: every rank here is a self-run **development proxy** (committed evaluator harness over
> reproducible public outputs), **not** an official score or leaderboard. Ranks are reported with their
> eligible field size for auditability; they are provenance, not a dominance claim.

## Scope

The census discovered 1,367 repositories, found 1,279 eligible repositories, and validated
672 public output artifacts. Comparisons use the same committed evaluator harness. Repository
availability and label coverage differ, so every rank is reported with its eligible field size.

## Overall position

| View | Main | V6 | Public position |
|---|---:|---:|---:|
| Seven-evaluator mean | 0.872686 | **0.906553** | **#1 / 673** |
| Strongest-union mean15 | 0.875238 | **0.910406** | **#1 / 100** |
| Equal four-axis balance | 0.832493 | **0.876596** | **#3 / 322** |
| H2 specialist | — | 0.884206 | #14 / 673 |
| Reviewer slice | 0.710627 | **0.809768** | #115 / 430 |
| Blind-recruiter slice | 0.871825 | **0.905858** | estimated #20 / 325 |

V6 wins all **30/30** tested composites against main across 15 evaluator families and two
missing-label policies. No measured public artifact dominates V6 simultaneously on H2,
mean7, reviewer, and blind-recruiter evidence.

## Strongest public archetypes reviewed

| Public archetype | What it does especially well | V6 response |
|---|---|---|
| `soy-praveen/redrob-ranker` | Highest H2 specialist score in the validated field | V6 accepts the specialist gap and wins the broader mean7/mean15 portfolio. |
| `candyflipgit/redrob-candidate-ranker` | Strong coherent-profile methodology and concise technical README | V6 adds broader evaluator coverage, exact release safety, API/demo proof, and 262-test regression evidence. |
| `shikhar1809/Sifter_Redrob_Hackathon` | Best human-label narrative, judge packet, validation ladder, and product screenshots | V6 uses its external recruiter labels as an independent cross-check, while outperforming its published output on V6's blind/reviewer comparison harness. |
| `0xSHSH/redrob-talentgraph-ai` | Strongest deployment clarity and polished full-stack README | V6 adds a Render Blueprint and deployment guide while retaining stronger broad ranking and release guarantees. |
| `rahulx2001/recruitgpt-x` | Clear separation of graded ranker and optional demo platform | V6 now states that separation explicitly in the judge packet and deployment guide. |

This is a comparison of public evidence and artifacts, not an official competition result or
a claim that V6 wins every isolated metric. The durable advantage is **all-around strength**:
ranking breadth, recruiter evidence, deterministic speed, failure safety, documentation, and
deployment readiness in one submission.

## Evidence trail

- Full tables: [`full_comparison_main_v3_v4_public.md`](full_comparison_main_v3_v4_public.md)
- V5/V6 ranking evidence: [`frontier_v5_experiment.md`](frontier_v5_experiment.md)
- Recruiter cross-check: [`external_recruiter_validation.md`](external_recruiter_validation.md)
- Main invariance: [`champion_main_invariance_audit.md`](champion_main_invariance_audit.md)
- Machine-readable values: [`metrics_manifest.json`](metrics_manifest.json)
