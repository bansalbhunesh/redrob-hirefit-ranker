# GAPS.md

Audit date: 2026-06-12 IST  
Project: `bansalbhunesh/redrob-hirefit-ranker`  
Hackathon: India Runs Track 1, Redrob AI x Hack2skill  
Deadline: 2026-06-28

---

## Lab Branch Pass — 2026-06-13 (codex/100-score-gap-lab)

Status of each original gap after the lab branch pass:

| Gap | Status | Evidence |
|---|---|---|
| P0 Gap 1 — Calibration CAND IDs | **Kept + CI-guarded** | `tests/test_no_cand_id_in_ranking_path.py` fails CI if CAND_ appears outside `calibration.py`. Evidence docstring in calibration.py unchanged. |
| P0 Gap 2 — Proxy-heavy evaluation | **Proxy still present** | No blind human labels added yet. Multi-JD transfer eval now covers 5 role families at 100K (all win vs keyword). Fairness counterfactual tests added. |
| P0 Gap 3 — No fairness audit | **Baseline implemented** | `tests/test_fairness_counterfactual.py` (12 tests), `docs/fairness_and_validity_audit.md`, README decision-support policy. |
| P1 Gap 4 — Architecture below SOTA | **Unchanged** | Backend transfer routing improved in `final_score()`. Full hybrid/reranker architecture requires structural work beyond the lab pass scope. |
| P1 Gap 5 — Sponsor alignment stops at CSV | **Partially improved** | API now has 12 routes, SQLite job store, auth gate. Multi-JD eval across 5 Redrob-aligned role families. Multilingual still absent. |
| P2 Gap 6 — Docker bind-mount SLA | **Documented, not solved** | VM-local Docker: 141s (pass). Windows bind-mount: 214s (above 200s). Cgroup-aware worker resolution deployed; mount I/O is the blocker. |
| Security scan | **Closed** | 0 bandit findings. `defusedxml` added, `torch` removed from research deps. HF Space CVE floors pinned. |
| DRY violation: `_cgroup_cpu_quota_count` | **Closed** | Extracted to `src/redrob_ranker/_cgroup.py`. Both `pipeline.py` and `retrieval.py` import from it. |
| In-memory job store | **Closed** | SQLite-backed `JobStore` in `apps/api/_job_store.py`. Jobs survive restarts. `audit_log` table persists every lifecycle event. |
| HF Space live vs local gap | **Documented** | `hf_space/requirements.txt` has MERGE GATE comment. Space is safe after merge+push. |

**Updated brutally honest score (lab branch after 2026-06-13 pass):** 91/100 vs main, 89/100 vs imaginary champion with blind human labels.

---

This report compares the current repo against the best submission that could exist for this hackathon, not against average hackathon entries.


## Champion Baseline

The champion submission for Track 1 is a compressed production talent-intelligence system:

- Multi-stage ranking: lexical retrieval, semantic retrieval, structured feature scoring, learned or listwise reranking, calibrated scores, and deterministic fallback paths.
- Evidence-grade evaluation: hidden-label humility, non-circular labels, blind held-out annotation, public benchmark sanity checks, ablations, bootstrap confidence intervals, and no candidate-ID tuning in the official ranking path.
- Recruiter trust: grounded reasons, counterfactual comparison, manual-review flags, fairness/proxy audits, adversarial resume defenses, and score provenance.
- Redrob alignment: natural-language people search, job/candidate/company signal integration, multilingual readiness, scale/cost discipline, ATS/export workflow, and production-ish APIs.
- Submission polish: one-command Docker, CI, artifact freshness checks, a demo that does not drift from the repo, and a deck whose claims are all generated from committed artifacts.

Primary research sources are documented in `RESEARCH.md`. The most important external anchors are:

- Hack2skill India Runs official event page: https://hack2skill.com/event/india_runs/
- Redrob official product pages: https://redrob.io/, https://redrob.io/resume-ranker, https://redrob.io/people-search, https://redrob.io/job-search, https://redrob.io/company-search
- ConFit v1 job-candidate matching: https://arxiv.org/html/2401.16349v1
- ConFit v2 hard-negative training and E5 reranking: https://arxiv.org/html/2502.12361v1
- ConFit v3 LLM listwise reranking: https://arxiv.org/html/2605.09760v1
- Eightfold AI talent matching engineering writeup: https://eightfold.ai/engineering-blog/ai-powered-talent-matching-the-tech-behind-smarter-and-fairer-hiring/
- Greenhouse Talent Matching docs: https://support.greenhouse.io/hc/en-us/articles/41396009937307-Talent-Matching
- hireEZ ResumeSense / Applicant Review: https://hireez.com/applicant-review/
- RecruiterX xAI hackathon winner: https://devpost.com/software/recruiterx

## Scores Against The Champion

| Dimension | Current submission | Champion bar | Score |
|---|---:|---|---:|
| Technical depth | Deterministic BM25 + 28 feature matrix + guardrails + calibration | Hybrid lexical/semantic retrieval, learned/listwise reranking, calibrated trust layer | 6.5/10 |
| ML rigor | Good ablations, but proxy labels, shared LLM samples, ID-level calibration | Blind held-out labels, no ID tuning, real/public benchmark validation | 4/10 |
| Result quality | Likely strong on this synthetic JD and output format | Strong under hidden labels, role transfer, and adversarial resumes | 6/10 |
| Reproduction safety | Docker, pinned deps, CI, 105 tests passing | Full artifact freshness, benchmark gates, data membership validation, no stale scripts | 7/10 |
| Demo quality | Render/FastAPI/Gradio demos, feature payloads | Production-like recruiter workflow, durable jobs, exports, freshness sync | 7/10 |
| Presentation | Strong README/docs/polished deck | Single source of truth, no metric ambiguity, no stale artifacts | 7/10 |
| Sponsor alignment | Good resume ranker story and behavioral signals | Redrob OS: people/job/company search, multilingual, graph, CRM/ATS workflow | 6/10 |
| Generalizability | One challenge JD, hand dictionaries, challenge-specific canonical compile, ID calibration | Multiple JDs, multilingual, transferable scorer | 3/10 |
| Reasoning quality | Grounded snippets and feature audit are strong | Pairwise explanations, uncertainty, fairness/manual-review flags | 7/10 |
| Deployment story | Demo API, in-memory jobs, one worker, no auth/persistence | Tenant-safe service, queues, audit logs, persistent results, integrations | 4/10 |

Overall against champion: 5.7/10.

## Intentional Design Decisions

These are not accidental defects:

- The official ranker is offline and deterministic by design. That is defensible for Hack2skill reproduction and Stage 3/4 constraints.
- Hosted LLMs are kept out of the ranking path. That is defensible because the official run must be reproducible and budget-safe.
- Static dense embeddings were tested and rejected under the repo's CPU/time budget. The decision is documented in `README.md:51`, `METHODOLOGY.md:45`, and `docs/ARCHITECTURE.md:40`.
- The repo intentionally values explainable hand features over a black-box learned scorer. That is defensible for auditability.
- Availability and honeypot handling are deliberate. The JD asks to down-weight unavailable candidates, and the honeypot audit is documented.

These decisions still create gaps versus a champion submission when they reduce transfer, semantic recall, fairness coverage, or perceived ML sophistication.

## P0 Gap 1 - Candidate-ID Calibration In The Official Path

What the gap is:

The official ranking path applies an explicit list of candidate-ID swaps for the bundled challenge JD. The calibration module contains exact candidate IDs and pairwise preferences (`src/redrob_ranker/calibration.py:32`). The pipeline applies it by default after ranking (`src/redrob_ranker/pipeline.py:168`). The project's own agent guidance calls "Candidate-ID hard-coding" dangerous (`.prompts/AGENTS.md:20`).

Worse, scores remain attached to positions, not candidates. The module says "Submission scores stay attached to POSITIONS" (`src/redrob_ranker/calibration.py:25`) and then emits `scores[i]` for the candidate now occupying that rank. That preserves monotonic CSV scores but weakens the meaning of score as model confidence.

What the champion does instead:

A champion learns or validates a general reranker over candidate features, pairwise comparisons, or listwise judgments. It never encodes `CAND_0068811` over `CAND_0001610` in source code. It can explain why one candidate moves above another without needing candidate identity.

Evidence:

- Local: `src/redrob_ranker/calibration.py:32-41`, `src/redrob_ranker/calibration.py:54-71`, `src/redrob_ranker/pipeline.py:168-171`.
- Local contradiction: `.prompts/AGENTS.md:20`.
- External: ConFit v2 and v3 improve rankings through model architecture, hard negatives, and listwise reranking, not ID swaps: https://arxiv.org/html/2502.12361v1 and https://arxiv.org/html/2605.09760v1.
- Official challenge asks for a robust POC that ranks candidates by relevance, not post-hoc row surgery: https://hack2skill.com/event/india_runs/.

Closeability:

Closeable before 2026-06-28, but painful because the current submission score may depend on it.

Exact fix:

- Remove `CALIBRATION_PREFERENCES` from the official path.
- If ordering changes are still needed, implement a no-ID pairwise reranker using existing features and source evidence.
- Add a test that fails if `src/redrob_ranker/` contains `CAND_` outside fixtures/tests.
- Recompute scores after reranking so each row's score belongs to that candidate.
- Document the metric delta honestly instead of preserving a positional score ladder.

## P0 Gap 2 - Evaluation Is Still Proxy-Heavy And Selection-Biased

What the gap is:

The repo has a lot of evaluation, but it is not gold evaluation. The "independent" labeler explicitly says the old silver labels were circular and that the new labeler is "still a HEURISTIC proxy" (`scripts/build_independent_labels.py:2-16`). The LLM judge story is stronger than most hackathon repos, but all three judge families score the same 249 candidate IDs (`docs/llm_judge_eval_2.md:4`, `docs/llm_judge_eval_3.md:3`). The calibration holdout admits low power: `0/279` contradiction rate and same sampled IDs (`docs/llm_judge_eval_3.md:33-34`, `docs/swap_holdout_validation.md:16`).

That means the evidence mostly says: "This ranker is consistent with its own proxy world." It does not prove champion-grade hidden-label generalization.

What the champion does instead:

A champion creates independent blind evaluation with fresh candidates, multiple baselines, stratified near-tie samples, and labels that are not selected around the submitted top 100. It reports confidence intervals and failure cases, and it uses held-out labels for final validation only.

Evidence:

- Local: `scripts/build_independent_labels.py:14`, `docs/ablation_ladder.md:7-10`, `docs/llm_judge_eval_2.md:4`, `docs/llm_judge_eval_3.md:3`, `docs/llm_judge_eval_3.md:33-45`, `docs/top100_ordering_audit.md:51`.
- External: Hack2skill precedent rewards technical implementation, model validation, reproducibility, and impact, not just polished claims; see the Hack2skill precedent links in `RESEARCH.md`.
- External: SOTA job-matching papers report MAP, nDCG, and recall under benchmark-style splits, not only same-sample LLM confirmations: https://arxiv.org/html/2401.16349v1.

Closeability:

Partly closeable before 2026-06-28.

Exact fix:

- Generate a new blind sample after freezing the current ranking: top 200 from current, BM25 baseline, dense baseline, LTR challenger, random near-threshold, and adversarial resumes.
- Label with at least two judges using pairwise comparisons and do not reuse the old 249-only set.
- Publish bootstrap confidence intervals for top-10, top-50, and top-100 deltas.
- Separate "used for tuning" labels from "final audit" labels in a manifest.
- Do not let calibration use the final audit set.

## P0 Gap 3 - No Fairness, Protected-Attribute, Or Legal-Risk Audit

What the gap is:

There is no serious fairness or hiring-compliance layer. Searches for fairness, protected attributes, gender, race, counterfactual testing, EEOC-style constraints, or manual-review policy turn up generic audit language, not an implemented fairness evaluation. The system uses location, company prestige, availability, recruiter responsiveness, profile views, endorsements, and social/activity signals. Those are exactly the kinds of proxy features that can encode protected or socioeconomic bias.

What the champion does instead:

A champion treats AI recruiting as a high-risk decision-support system. It includes protected/proxy-feature sensitivity tests, counterfactual profile swaps, adverse-impact checks where labels allow it, manual-review language, uncertainty flags, and an explicit "assistive ranking, not automated rejection" policy.

Evidence:

- Local: heavy use of behavioral and location/company signals in `src/redrob_ranker/features.py`; no matching fairness test suite under `tests/`.
- External: Greenhouse AI docs emphasize human control, scorecards, matching explanations, and admin controls: https://support.greenhouse.io/hc/en-us/articles/33043749845403-Greenhouse-AI-features and https://support.greenhouse.io/hc/en-us/articles/41396009937307-Talent-Matching.
- External: Eightfold's talent matching writeup frames fairness and explainability as core to hiring AI: https://eightfold.ai/engineering-blog/ai-powered-talent-matching-the-tech-behind-smarter-and-fairer-hiring/.
- External: Recent research on LLM resume screening warns about discrimination, construct validity, and job-relatedness risk; see fairness paper links in `RESEARCH.md`.

Closeability:

Closeable enough for hackathon before 2026-06-28.

Exact fix:

- Add a `docs/fairness_and_validity_audit.md`.
- Add counterfactual tests: same profile with changed name, gender-coded fields, language, location, college tier, and non-work demographic proxies.
- Report score deltas and rank deltas.
- Add a "fair mode" ablation that removes location, response-rate, profile views, endorsements, and company-prestige proxies, then compares quality.
- Add manual-review flags for low-confidence, proxy-heavy, or near-threshold candidates.
- Make the README explicitly state this is decision support, not automated rejection.

## P1 Gap 4 - Ranking Architecture Is Below Current SOTA

What the gap is:

The official architecture is BM25 plus a handcrafted 28-feature matrix. That is engineered well, but it is not SOTA for job-candidate matching. The repo rejects static dense embeddings and learned challengers under its own tests (`README.md:51-61`, `docs/ltr_challenger_study.md:13-39`), but those tests do not cover the best champion path: hybrid retrieval plus a stronger top-K reranker, hard negatives, or listwise reranking.

What the champion does instead:

A champion uses lexical retrieval for recall, dense bi-encoder retrieval for semantic matching, and a cross-encoder/listwise reranker over the top candidates. It can still keep the final run deterministic by using local models, cached embeddings, or a documented CPU-safe top-K stage.

Evidence:

- Local: `README.md:51-54` says ConFit-class fine-tuned transformer encoders are infeasible under the CPU budget, not tested.
- Local: `docs/ARCHITECTURE.md:40-49` acknowledges retrieve + dense rerank + cross-encoder/LLM rerank is the research pattern, then chooses not to ship it.
- External: ConFit v1/v2/v3 show job-candidate matching gains from contrastive retrieval, hard negatives, and listwise LLM reranking: https://arxiv.org/html/2401.16349v1, https://arxiv.org/html/2502.12361v1, https://arxiv.org/html/2605.09760v1.
- External: Redrob itself is an AI/search company; a judge will expect modern semantic retrieval awareness.

Closeability:

Partly closeable. Full ConFit-level training is structural. A top-K semantic/listwise reranker is closeable if scoped.

Exact fix:

- Keep BM25 + features as candidate generation.
- Add a top-500 or top-1000 reranker that uses no candidate IDs and is benchmarked under the 300s CPU budget.
- If no model improves quality, document a stronger negative result than the current static-embedding gate: include recall@K, overlap analysis, near-tie judge eval, and failure examples.
- Consider a local cross-encoder only on top 200 if runtime permits; otherwise add a pairwise feature reranker trained on blind LLM labels.

## P1 Gap 5 - Sponsor Alignment Stops At Resume Ranking

What the gap is:

The repo aligns with Redrob's Resume Ranker product, but not with the wider Redrob OS story: people search, job search, company search, multilingual profiles, company/contact graph, CRM/export workflow, and natural-language recruiter queries. The current JD compiler is rule-based and challenge-shaped. The repo admits the tokenizer is Latin-only and deletes Devanagari (`src/redrob_ranker/text.py:10`, `docs/ARCHITECTURE.md:62-66`).

What the champion does instead:

A champion makes Redrob think: "This plugs into our roadmap." It would show a recruiter query, candidate search, company context, job-fit reasoning, export, multilingual handling, and product workflow, not just a CSV ranker.

Evidence:

- Local: `src/redrob_ranker/text.py:10` tokenizes only `[a-z0-9_+#.]+`.
- Local: `docs/ARCHITECTURE.md:62-66` acknowledges Indic-script deletion.
- Local: JD compiler has challenge canonical behavior (`src/redrob_ranker/jd_compiler.py:18`, `src/redrob_ranker/jd_compiler.py:242-250`).
- External: Redrob product pages emphasize people search, job search, company search, match scores, language support, and clean shortlist/export workflows: https://redrob.io/people-search, https://redrob.io/job-search, https://redrob.io/company-search, https://redrob.io/resume-ranker.

Closeability:

Partly closeable before 2026-06-28.

Exact fix:

- Add a "Redrob OS mode" demo tab: recruiter query -> compiled JD signals -> ranked shortlist -> candidate/company evidence -> CSV export.
- Add Unicode-aware tokenization tests for Hindi/Devanagari and common Indian language profile fields.
- Add 5 non-challenge JD fixtures and show ranker behavior shifts.
- Add company-signal summaries using existing candidate company fields, even if shallow.

## P1 Gap 6 - Generalizability Is Weak

What the gap is:

The system is highly tuned to the Senior AI Engineer JD. Constants, phrase dictionaries, role weights, disqualifiers, and title weights are hand-curated. The compiler explicitly keeps the bundled challenge JD byte-identical to the default configuration (`src/redrob_ranker/jd_compiler.py:18`, `src/redrob_ranker/jd_compiler.py:80-92`). If the judge asks for a different Redrob role, this is not yet a convincing general ranker.

What the champion does instead:

A champion demonstrates transfer. It runs multiple JDs, explains which skills and signals changed, and has tests showing that frontend, backend, AI, data, and sales roles do not all collapse into the same AI-engineering ranking.

Evidence:

- Local: `src/redrob_ranker/constants.py` is the real scoring substrate.
- Local: `src/redrob_ranker/jd_compiler.py:100-130` contains hard-coded triggers, aliases, and weights.
- Local: `src/redrob_ranker/jd_compiler.py:242-250` emits the canonical query for the challenge concept set.
- External: Redrob People Search promises natural-language search and intent parsing across profiles, not one frozen JD: https://redrob.io/people-search.

Closeability:

Closeable at demo level, structural at model level.

Exact fix:

- Add a `docs/generalization_suite.md` with 5-10 JDs and expected top-signal shifts.
- Add tests that compile these JDs and verify changed weights/query terms.
- Run a small candidate sample through at least three role families and show distinct outputs.
- Remove or isolate the "challenge canonical" shortcut from generic JD behavior.

## P1 Gap 7 - Deployment Is Demo-Only, Not Product-Like

What the gap is:

The FastAPI app is an excellent demo, but it is not a production service. It uses in-memory job/result stores and explicitly warns that multiple uvicorn workers would break jobs/SSE (`apps/api/main.py:84-86`). Live ranking is capped at 500 candidates and batch ranking at 5000 (`apps/api/main.py:44-45`). There is no auth, tenant isolation, durable job storage, persistent audit log, queue, or ATS/CRM integration.

What the champion does instead:

A champion has a demo API plus a credible deployment story: background queue, durable result store, auth token, export endpoints, audit events, and a Render/Vercel/Railway deployment manifest. It does not need enterprise scale, but it should show the shape of production.

Evidence:

- Local: `apps/api/main.py:44-45`, `apps/api/main.py:84-86`, `apps/api/main.py:294-330`, `apps/api/main.py:355-395`.
- External: Greenhouse/Lever/hireEZ systems fit into ATS workflows and recruiter review pipelines: https://support.greenhouse.io/hc/en-us/articles/41396009937307-Talent-Matching and https://hireez.com/applicant-review/.

Closeability:

Closeable enough for hackathon.

Exact fix:

- Add an optional SQLite job/result store for demo persistence.
- Add a simple bearer token for public demo write endpoints.
- Add a background worker abstraction and job status table.
- Add `/api/export/greenhouse.csv` or generic ATS CSV export.
- Add a `render.yaml` or equivalent deployment manifest.

## P1 Gap 8 - Anti-Fraud And Adversarial Resume Robustness Are Too Narrow

What the gap is:

The honeypot layer catches synthetic contradictions and keyword stuffing, which is useful. It does not cover modern resume attacks: hidden text, HTML/PDF artifacts, prompt injection, Unicode confusables, inflated project claims, duplicated profiles, credential inconsistencies, or "ignore previous instructions" payloads embedded in resumes. The official ranker avoids hosted LLMs, so prompt injection is less dangerous during ranking, but the broader product/demo still ingests untrusted candidate text and presents evidence to humans.

What the champion does instead:

A champion includes adversarial resume fixtures and a fraud/readiness panel. It differentiates "skilled but overclaimed" from "malicious or unverifiable," and it shows judges the system will not reward obvious gaming.

Evidence:

- Local: honeypot handling exists (`docs/honeypot_audit.md`, `src/redrob_ranker/features.py:795`) but there is no comparable hidden-text/prompt-injection suite.
- External: hireEZ ResumeSense positions itself around analyzing resumes at scale and surfacing fit; production screening vendors increasingly treat resume parsing, false claims, and review workflow as core: https://hireez.com/applicant-review/.
- External: Reddit/practitioner research in `RESEARCH.md` shows candidate and recruiter distrust of opaque or gameable ATS scoring.

Closeability:

Closeable before 2026-06-28.

Exact fix:

- Add `tests/test_adversarial_resumes.py`.
- Include fixtures for hidden Unicode, prompt-injection text, repeated keyword blocks, fake current roles, impossible credential timelines, and copied profiles.
- Add visible "integrity flags" to API payloads and reasoning.
- Add a demo filter for "manual review required."

## P1 Gap 9 - Artifact Drift Undermines Trust

What the gap is:

Several public-facing artifacts disagree:

- `apps/api/data/precomputed.json:9` says `processing_time_ms` is `193000`.
- `docs/runtime_matrix.md:38-49` reports newer 124.7s and 138.3s runs.
- `hf_space/app.py:116` says `~104s`.
- `build_deck.py:155` still generates an older deck with `<=194s`.
- The polished deck appears patched by one-off scripts rather than generated from a single current source.

A judge seeing this will not know which number to trust.

What the champion does instead:

A champion has a single metrics manifest and generates README snippets, demo payloads, and deck KPI slides from it. CI fails if artifact numbers drift.

Evidence:

- Local: `apps/api/data/precomputed.json:9`, `hf_space/app.py:116`, `build_deck.py:155`, `docs/runtime_matrix.md:38-49`.

Closeability:

Closeable before 2026-06-28.

Exact fix:

- Create `docs/metrics_manifest.json`.
- Update `build_deck.py`, API precomputed metadata, Gradio demos, and README from that file.
- Add a test that parses these files and fails on stale KPI values.
- Delete or clearly mark obsolete deck-generation scripts.

## P1 Gap 10 - Reproduction Gates Are Good But Incomplete

What the gap is:

CI runs validation and tests, and they currently pass. But the full benchmark is not a normal code gate: `.github/workflows/cloud-benchmark.yml` only runs manually or when that workflow file changes (`.github/workflows/cloud-benchmark.yml:10-13`). The official candidate pool is local/ignored, and generated artifacts under `artifacts/` are mostly ignored (`.gitignore:14-19`). The old embedding gate script is out of sync with the current label API: it expects `tiers, gains = ev.load_labels(labels)` even though `load_labels` returns a `LabelSet` (`scripts/run_embedding_gate.py:46`, `src/redrob_ranker/eval_harness.py:80-93`).

What the champion does instead:

A champion has CI that proves the submitted artifact is fresh, validates candidate membership, runs a smoke benchmark, and keeps all documented experiments executable or explicitly archived.

Evidence:

- Local: `.github/workflows/ci.yml:23-35` is good but limited.
- Local: `.github/workflows/cloud-benchmark.yml:10-13`.
- Local: `.gitignore:14-19`, `.dockerignore:5-7`.
- Local: `scripts/run_embedding_gate.py:46`, `src/redrob_ranker/eval_harness.py:80-93`.

Closeability:

Closeable before 2026-06-28.

Exact fix:

- Run a benchmark smoke test on PR/push for generated 20K or 100K synthetic data.
- Add an artifact freshness test: rerun ranker on a small fixed sample and compare expected output hash.
- Fix `scripts/run_embedding_gate.py` or mark it archived.
- Add a data availability checklist for `candidates.jsonl` and expected SHA256 if allowed.

## P2 Gap 11 - Submission Validator Does Not Check Candidate Membership

What the gap is:

The validator checks header, row count, ID regex, duplicate IDs, ranks, and score monotonicity. It does not check that candidate IDs exist in the provided candidate pool (`src/redrob_ranker/validation.py:18-39`). This is not fatal for the current submission, but it is a weak validator for a ranker.

What the champion does instead:

A champion validator optionally takes the candidate JSONL and rejects IDs not present in the pool.

Evidence:

- Local: `src/redrob_ranker/validation.py:18-39`, `scripts/validate_submission.py:26`.

Closeability:

Closeable in under an hour.

Exact fix:

- Add `--candidates candidates.jsonl` to `scripts/validate_submission.py`.
- Load candidate IDs and reject unknown IDs.
- Add a test with a syntactically valid but nonexistent `CAND_9999999`.

## P2 Gap 12 - Metric Framing Can Read Like Hidden-Score Overclaim

What the gap is:

The README and deck surface `P@10 = 1.0`, `NDCG@10 = 0.894`, and composite scores prominently. The docs often qualify these as independent LLM/proxy metrics, but a first-pass judge could read them as official performance. That is dangerous because the evaluation is proxy-heavy and tuned.

What the champion does instead:

A champion labels every non-official metric as "dev proxy" or "LLM audit sample" in the headline itself. It avoids any ambiguity between official hidden score and internal validation.

Evidence:

- Local: `README.md:28`, `METHODOLOGY.md:65-70`, `build_deck.py:176`.
- Local: `docs/LLM_JUDGE_EVAL.md:5` does clarify dev-only LLM judge, but the headline KPI presentation is still easy to overread.

Closeability:

Closeable before 2026-06-28.

Exact fix:

- Rename all KPI labels to "Dev LLM-audit P@10" and "Dev proxy NDCG@10."
- Add a one-line "No official hidden labels were available" under the metric table.
- Use the same phrasing in README, deck, API demo, and Gradio demo.

## P2 Gap 13 - Reasoning Is Strong But Not Yet Champion-Level

What the gap is:

The reasoning rows are grounded and better than average. The remaining gap is pairwise and uncertainty reasoning. The system explains "why this candidate matches"; it does not consistently explain "why rank 18 is below rank 17," where most ranking disputes happen. Also, after positional calibration, the displayed rank score can diverge from the candidate's underlying feature total.

What the champion does instead:

A champion provides adjacent-candidate comparisons, uncertainty bands, and flags when two candidates are effectively tied. It can show a recruiter which evidence moved the ordering.

Evidence:

- Local: reasoning is template/feature based in `src/redrob_ranker/reasoning.py`.
- Local: positional-score behavior is documented in `src/redrob_ranker/calibration.py:25-27`.
- External: Redrob Resume Ranker promises side-by-side comparison and objective team decisions: https://redrob.io/resume-ranker.

Closeability:

Closeable at demo level.

Exact fix:

- Add pairwise diff explanations for adjacent top-25 candidates.
- Add an "effective tie" flag where score gap is under a threshold.
- In the API payload, show candidate raw score, calibrated score, and rank reason separately.

## What Moves Prize Probability Most

1. Remove or replace candidate-ID calibration, then publish a fresh blind evaluation pack.
   This is the biggest trust repair. If a judge notices `CAND_` swaps in the official path, the repo's credibility takes a direct hit.

2. Add a fairness/proxy/adversarial audit with visible demo flags.
   This turns the repo from "clever ranker" into "responsible hiring AI," which is closer to what a Redrob judge has to defend publicly.

3. Sync artifacts and deepen Redrob product alignment.
   Make the demo/deck/README pull from one metrics manifest, add multilingual/tokenization evidence, and show recruiter query -> shortlist -> audit -> export.

## Verdict

Realistic prize probability: 20%.  
Realistic winner probability: 8%.

This assumes the actual field contains many shallow LLM wrappers and keyword matchers. If even one competing team ships a clean hybrid reranker with blind labels, fairness controls, and a polished Redrob-like workflow, this repo loses on ML rigor and product alignment.

What a Redrob judge says when opening this repo:

"This is serious. It runs, it is documented, it understands the challenge JD, the output is clean, and the demo is useful. But it is also heavily challenge-specific, proxy-evaluated, and has candidate-ID calibration in the official path. I can admire the engineering and still not trust it as a general Redrob product layer."

What the judge says when opening the champion repo:

"This is a hiring-intelligence product prototype: modern retrieval/reranking, blind evaluation, fairness and fraud controls, multilingual readiness, auditability, export workflow, and no leaderboard-looking hacks. This is exactly the direction Redrob can use."

