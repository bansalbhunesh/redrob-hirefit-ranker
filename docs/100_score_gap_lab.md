# 100 Score Gap Lab

Branch: `codex/100-score-gap-lab`  
Status: local-only experiment branch. Do not push or merge until an experiment has evidence.

This branch exists to explore what would move the project from prize-competitive to dominant without disturbing the frozen `main` submission.

## Research Snapshot

Fresh external signals checked on 2026-06-12:

- India Runs Track 1 asks for intelligent candidate discovery beyond surface keywords, with GitHub code, documentation, and ranked output: https://hack2skill.com/event/india_runs
- Redrob's public product story is broader than resume ranking: Resume Ranker, People Search, Job Search, Company Search, APIs, multilingual and emerging-market positioning: https://redrob.io/, https://redrob.io/resume-ranker, https://redrob.io/people-search, https://redrob.io/job-search, https://redrob.io/company-search
- ConFit v3 frames the current research frontier as retrieve first, then LLM/listwise rerank for person-job fit, with controllability and explainability as the adaptation problem: https://arxiv.org/html/2605.09760v1
- Recent resume-screening validity work argues for ground-truth-controlled, paired audits rather than surface selection-rate claims: https://arxiv.org/html/2602.18550v1
- Multi-agent resume screening work separates extraction, evaluation, summarization, and score formatting for explainability: https://arxiv.org/html/2504.02870v1
- Greenhouse Talent Matching emphasizes candidate opt-out, "Needs manual review", disclaimers, GDPR/data retention setup, and human-controlled review workflows: https://support.greenhouse.io/hc/en-us/articles/41131616864283-Talent-Matching-Data-Processing-FAQ and https://support.greenhouse.io/hc/en-us/articles/48563080657435-Talent-Matching-setup
- Greenhouse Real Talent positions fraud detection, identity verification, and talent matching as one trust layer: https://www.greenhouse.com/real-talent-candidate-matching

## Actual Remaining Gap To Winner

The main repo is no longer missing basic hackathon hygiene. The gap is not tests, docs, Docker, or demo polish. The real gap is judge trust under adversarial review:

1. Calibration optics: candidate-ID calibration remains the one easy reputational attack.
2. Evaluation confidence: dev-proxy labels are honest, but not fresh blind labels.
3. Responsible hiring proof: fairness/proxy, manual-review, and fraud/adversarial controls are thinner than production HR AI systems.
4. Redrob OS framing: the system reads as a strong ranker, not yet as a mini people/job/company intelligence layer.
5. Generalization proof: the challenge JD is deeply handled; several non-challenge JDs would prove transfer.

## Experiments Worth Testing Locally

### Experiment A - Counterfactual proxy audit

Goal: show the system is auditable under controlled profile edits.

Branch artifact:

- `scripts/counterfactual_proxy_audit.py`
- `tests/test_counterfactual_proxy_audit.py`

What it tests:

- Name neutralization should not move score.
- Location/proxy edits should show explicit, measurable deltas.
- Behavioral-signal edits should be visible as recruiter-process signals, not hidden magic.

Merge bar:

- Full test suite passes.
- Audit can run on full `candidates.jsonl` and produce a small report.
- README/deck framing must say "proxy sensitivity audit", not "bias eliminated".

### Experiment B - Fresh blind mini-eval

Goal: close the most important eval attack without building a new model.

Protocol:

- Freeze the current main ranker.
- Sample candidates from current top 100, BM25 top 100, optional dense/LTR challenger top 100, near-threshold ranks, and random background.
- Label with pairwise prompts that do not reveal current rank.
- Use at least two judge families.
- Tune nothing on this set.

Merge bar:

- Current ranker beats BM25 and keyword baselines on the fresh sample.
- If it loses to a challenger, do not merge docs claiming dominance.
- Publish confidence intervals and failure cases.

### Experiment C - No-ID calibration challenger

Goal: find whether the 8 hard-coded swaps can be replaced by a general rule.

Protocol:

- Remove candidate IDs from the calibration logic in an experiment branch.
- Train or hand-build a pairwise feature preference function using only feature deltas and source evidence.
- Compare top-100 composite under existing proxy labels and fresh blind mini-eval.

Merge bar:

- No `CAND_` literals in `src/redrob_ranker/` outside tests/fixtures.
- Golden output changes only if the quality evidence is better and the deck can defend the change.
- Scores remain candidate-owned, not positional.

### Experiment D - Adversarial resume/fraud audit

Goal: show the ranker does not reward obvious gaming.

Fixtures:

- Hidden keyword blocks.
- Prompt-injection text.
- Unicode confusables.
- Impossible timelines.
- Fake current role inflation.
- Copied/near-duplicate profile text.

Merge bar:

- Each fixture either triggers a flag or fails to improve rank materially.
- Demo can show "manual review required" for integrity flags.

### Experiment E - Redrob OS demo framing

Goal: make the judge see a Redrob scoring layer, not a CSV script.

Scope:

- Recruiter query/JD input.
- Compiled hiring intent.
- Ranked shortlist.
- Candidate evidence.
- Company/context signals from existing fields.
- CSV export.

Merge bar:

- No new fragile backend dependency.
- Demo remains fast and deterministic.
- No stale metric drift.

## What Not To Do

- Do not start a large reranker unless it can beat the current system within 24-48 hours and stay under runtime budget.
- Do not make fairness claims without counterfactual evidence.
- Do not force-push or rewrite the frozen main artifact.
- Do not merge branch-only experiments that change `submission.csv` without a deliberate decision.
- Do not add a half-built production API story; it is worse than saying "demo service".

## First Local Test Command

```bash
python scripts/counterfactual_proxy_audit.py --candidates demo_sample.jsonl --out artifacts/counterfactual_proxy_audit_demo.csv --max-candidates 5
```

The output belongs in ignored `artifacts/` unless a summarized report is deliberately promoted.

## First Branch Result

Command run:

```bash
python scripts/counterfactual_proxy_audit.py --candidates demo_sample.jsonl --out artifacts/counterfactual_proxy_audit_demo.csv --max-candidates 5
```

Result:

- 20 counterfactual rows written.
- Name neutralization delta was 0.0 on sampled rows, as desired.
- Preferred India location and behavioral-neutral edits produced explicit, inspectable deltas.
- This is useful as an audit harness, not as a claim that bias is solved.

## Full Proxy Audit Result

Command run on the full local pool:

```bash
python scripts/counterfactual_proxy_audit.py --candidates candidates.jsonl --out artifacts/counterfactual_proxy_audit_100k.csv --max-candidates 100000
python scripts/summarize_counterfactual_proxy_audit.py --audit artifacts/counterfactual_proxy_audit_100k.csv --out artifacts/counterfactual_proxy_audit_100k_summary.json
```

Result:

- 100,000 candidates, 400,000 counterfactual rows.
- Runtime: 556.3 seconds.
- Name-neutralized score deltas: 0 / 100,000 nonzero.
- Location and behavioral edits produced measurable deltas; see `docs/fairness_and_proxy_audit.md`.

## Additional Branch Improvements

- VM/runtime: `docs/vm_runtime_lab.md` documents the cgroup CPU quota worker-cap
  fix. On this Docker Desktop VM, constrained 100K runtime improved from 422.9s
  to 120.7s with byte-identical output.
- Adversarial integrity: `docs/adversarial_integrity_audit.md` documents
  prompt-injection, hidden-text, and repeated-keyword detection. Full-pool scan
  flags 0 profiles after threshold tuning.
- JD generalization: `docs/generalization_probe.md` documents supported
  AI/search/backend JDs and fail-closed behavior for an unsupported sales role.
- Calibration transparency: `docs/calibration_transparency_lab.md` documents
  the `--no-calibration` audit mode and real 100K diff against the submitted
  output.

## External / Multi-JD Evidence Added

- External public pairwise fit eval:
  `docs/external_blind_pairwise_eval.md` scores the Hugging Face
  `cnamuangtoun/resume-job-description-fit` test split. Current result is
  diagnostic, not a trophy: HireFit AUC 0.5458 vs keyword-overlap 0.5549 on
  1,317 supported technical rows. This does **not** close the official hidden
  label gap; it proves the harness and shows where transfer is still thin.
- Multi-JD Redrob-pool transfer eval:
  `docs/multi_jd_generalization_eval.md` scores 20,000 candidates across five
  technical JDs with independent raw-field role rubrics. After the role-depth
  and surface/title tuning patches, mean composite is 0.7899 vs keyword baseline
  0.6793. `docs/multi_jd_generalization_eval_100k.md` repeats the same benchmark
  across the full 100,000-candidate pool: mean composite is 0.7613 vs keyword
  baseline 0.6602. The prepared corpus/index path keeps all 100K role timings
  below 50 seconds after a 73.2 second one-time setup. The win is still uneven:
  AI/search/data-BI/devops beat keyword at both sizes, while backend improved
  sharply but still trails the keyword oracle by 0.0418 on 20k and 0.0040 on
  100k.
- Compiler/scoring expansion:
  alternate technical JDs now get role-family priors, role-evidence reuse,
  transfer-specific risk handling, current-title/history safeguards,
  backend/data depth extractors, backend surface coverage, data-primary title
  separation, backend-primary evidence/coverage calibration, stricter
  current-title dominance, and reusable BM25 corpus/index preparation for
  multi-JD transfer runs. The bundled challenge JD remains golden-gated and
  byte-identical.
- External role-depth mining:
  `docs/external_role_depth_terms.md` scans the downloaded public datasets and
  finds 20,668 backend/platform rows and 17,163 data/BI rows supporting the
  backend API/database/scale/infra and data SQL/warehouse/viz/ETL/impact
  lexicons. This is lexicon provenance, not hidden-label evidence.
