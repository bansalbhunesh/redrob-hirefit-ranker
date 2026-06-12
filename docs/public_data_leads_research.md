# Public Data Leads Research

Branch: `codex/100-score-gap-lab`  
Scope: public, unauthenticated sources only. No logged-in X/Twitter scraping, no protected
LinkedIn scraping, no CAPTCHA bypassing, no private personal-data harvesting.

## Brutal Verdict

There is no public Redrob hidden-label dataset on the open web. Scraping Reddit, X, LinkedIn,
or random ATS blogs will not produce the one thing that makes the submission 95+:
independent, blind relevance labels on the actual Redrob-style candidate pool.

What public research can do:

- prove sponsor alignment against Redrob and Hack2Skill's own wording;
- provide external resume/JD fit datasets for transfer tests;
- expose real recruiter/candidate failure modes for adversarial audits;
- identify public baselines and SOTA papers to benchmark against;
- sharpen the exact remaining gap: role-transfer and non-official-label proof.

What public research cannot honestly do:

- recover the hidden evaluation labels;
- prove the official top 100 is optimal;
- make Reddit/X chatter equivalent to a labeled ranking benchmark;
- justify stealth scraping protected sites as a deadline strategy.

## Official Bar

Sources:

- Hack2Skill India Runs: https://hack2skill.com/event/india_runs
- Redrob homepage: https://redrob.io/
- Redrob Resume Ranker: https://redrob.io/resume-ranker
- Redrob People Search: https://redrob.io/people-search
- Redrob Job Search: https://redrob.io/job-search
- Redrob Company Search: https://redrob.io/company-search

What the official pages say the winner must look like:

| Source | Ground truth signal | Consequence for this repo |
|---|---|---|
| Hack2Skill Track 1 | Deep JD understanding, contextual relevance beyond keywords, use of profile/career/activity signals, fast ranked shortlist | The current deterministic feature ranker is aligned with the challenge shape. Any change that slows the official path or hides reasoning is a regression. |
| Hack2Skill timeline | Track 1 closes June 28, 2026; evaluation runs July 3-16, 2026; finale July 22, 2026 | No giant architecture rewrite. Only measured, isolated lab improvements should be considered. |
| Redrob homepage | 700M+ profiles, 30+ languages, real data across hiring/sales/jobs/research | A Resume Ranker-only story is good but not maximum sponsor alignment. The product story should show how ranking plugs into Redrob OS. |
| Redrob Resume Ranker | Skill alignment, experience depth, credentials, side-by-side applicant comparison, ranked shortlist | Your strongest current lane. The repo should keep foregrounding traceable skill/experience/relevance evidence. |
| Redrob People Search | Natural-language people search across 700M+ profiles, role/skill/company/intent signals, verified contact/export/CRM workflows | Missing champion-grade product depth: recruiter search, company/contact evidence, CRM/export story beyond CSV. |
| Redrob Job Search | 15M+ listings, skill-first ranking, match score per job, Hindi/Tamil/Telugu/Marathi plus 27 more Indian languages | Current Latin-only tokenizer and role-specific weights are the honest weakness. Multilingual is sponsor-important but risky to half-build. |
| Redrob Company Search | Company intelligence, hiring signals, tech stack and decision-maker context | Current repo has almost no company graph or employer intelligence layer. This is a sponsor-alignment gap, not an official CSV gap. |

## Public Dataset Leads

The collector script is `scripts/research_public_data_leads.py`. It records public metadata into
`artifacts/public_data_leads.json` so the lead list is repeatable without changing the ranking path.

| Dataset | URL | Label / data type | Usefulness | Brutal call |
|---|---|---|---|---|
| `cnamuangtoun/resume-job-description-fit` | https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit | Resume text, JD text, `Good Fit` / `Potential Fit` / `No Fit` | Already used in `docs/external_blind_pairwise_eval.md` | Useful but currently exposes weakness: HireFit AUC 0.5458 vs keyword 0.5549. Keep it as honest transfer evidence, not a trophy. |
| `0xnbk/resume-ats-score-v1-en` | https://huggingface.co/datasets/0xnbk/resume-ats-score-v1-en | Resume-like text, numeric ATS score, original fit label | Good next external regression/classification check | Closeable: add an evaluator that maps ATS score to tier and compares ranker score vs keyword/embedding baseline. |
| `facehuggerapoorv/resume-jd-match` | https://huggingface.co/datasets/facehuggerapoorv/resume-jd-match | Prompt-style JD/resume pair plus label | Likely derived from the same source family as `cnamuangtoun` | Use only after duplicate check. Do not count it as independent if rows overlap. |
| `layan009/RESUMES-JOBS-FIT-LABELS` | https://huggingface.co/datasets/layan009/RESUMES-JOBS-FIT-LABELS | Resume text, JD text, fit label, metadata zip | Promising but appears row-compatible with `cnamuangtoun` in samples | Inspect for duplicate rows first. If duplicate, it is not new evidence. |
| `netsol/resume-score-details` | https://huggingface.co/datasets/netsol/resume-score-details | JSON resume-score details, likely LLM-generated scoring/rationale | Good for reasoning-schema comparison and score calibration language | Not strong gold labels. Use for explanation/rubric comparison, not official ranking proof. |
| `emrekuruu/job-search-distill` | https://huggingface.co/datasets/emrekuruu/job-search-distill | Job evals, jobs, generated query pairings, resume corpus | Useful for Redrob Job Search story and query-to-job transfer | Not direct candidate ranking unless evaluator is built. Good for demo/product depth. |
| `AzharAli05/Resume-Screening-Dataset` | https://huggingface.co/datasets/AzharAli05/Resume-Screening-Dataset | Role, resume, decision, reason, JD | Useful for accept/reject sanity and explanation robustness | Synthetic-looking and noisy. Treat as adversarial/generalization check, not gold. |
| `batuhanmtl/job-skill-set` | https://huggingface.co/datasets/batuhanmtl/job-skill-set | Job title, JD, extracted skill set | Good for JD compiler and skill extraction tests | Not a resume ranking benchmark. |
| `jacob-hugging-face/job-descriptions` | https://huggingface.co/datasets/jacob-hugging-face/job-descriptions | Job descriptions and generated structured fields | Good for JD parsing/normalization tests | Tiny; use for compiler regression, not scoring proof. |

### Immediate Dataset Build Plan

Closeable before deadline:

1. Add `0xnbk` external evaluator.
   Measure Spearman/Pearson against ATS score and AUC against original fit label. If HireFit still loses to keyword, report it honestly and use it to tune only the non-official lab branch.

2. Add duplicate detector across `cnamuangtoun`, `facehuggerapoorv`, and `layan009`.
   These look related. Counting them as three independent proofs would be fake rigor.

3. Add one “non-AI technical role” transfer evaluator.
   Backend, DevOps, and BI remain weaker because the current feature system is deliberately optimized for the Senior AI/Search JD. The multi-JD lab already proves this: Backend composite 0.4757 vs keyword 0.7120; Data/BI 0.7328 vs keyword 0.8061; DevOps 0.5957 vs keyword 0.6595.

4. Add a blinded challenge-pool judge pack, if the candidate pool is available locally.
   Sample candidates after freezing the official ranking: submitted top 100, keyword top 100 misses, near-threshold candidates, role-family candidates, random controls, and adversarial profiles. Judge with at least two independent LLM rubrics or humans. This is the closest available substitute for hidden labels.

Structural / not honestly closeable by scraping:

- official hidden Redrob labels;
- real recruiter outcome labels;
- production Redrob graph/contact/company data;
- trustworthy multilingual candidate matching without real multilingual candidate profiles and tests.

## Reddit Threads

Sources checked through public old Reddit HTML:

- https://old.reddit.com/r/recruitinghell/comments/1gvcpz4/ai_resume_screening_should_be_illegal/
- https://old.reddit.com/r/recruitinghell/comments/1lk9uty/employers_are_buried_in_aigenerated_r%C3%A9sum%C3%A9s/
- https://old.reddit.com/r/cscareerquestions/comments/1kt12kw/whats_the_best_way_to_get_through_ai_job_filters/
- https://old.reddit.com/r/MachineLearning/comments/cmihda/d_company_hirevue_provides_ai_for_earlystage/

Usable signals:

- Candidates think AI screening is opaque, keyword-driven, and gameable.
- Applicants actively tailor resumes to pass ATS/AI filters.
- Recruiters are facing AI-generated resume floods, which makes fraud/integrity checks more important.
- ML practitioners are skeptical of black-box hiring signals that are not job-related.

What to build from this:

- Keep the adversarial integrity audit visible: hidden text, prompt injection, bogus perfect-on-paper resumes, keyword stuffing.
- Keep explanations grounded in candidate facts, not generic LLM prose.
- Add a one-page “assistive ranking, not auto-rejection” policy if presentation space allows.
- Do not train on Reddit comments. They are qualitative product-risk evidence, not labels.

## X/Twitter, LinkedIn, And Social Scraping

Public search-index queries for Redrob + India Runs + candidate ranking did not produce reliable
label data. X and LinkedIn are mostly login/protection-gated for structured collection. The right
decision is to record “not usable” rather than burn time on brittle or questionable scraping.

Use social sources only for:

- public announcements;
- demo screenshots if the page is publicly accessible;
- qualitative claim discovery.

Do not use social sources for:

- candidate labels;
- training data;
- personal contact harvesting;
- claims that require bypassing auth, rate limits, or bot protections.

Scrapling note: the attached Scrapling repo is a capable scraping framework, but the stealth and
Cloudflare-solving modes are the wrong risk profile for this hackathon. A dependency-light public
collector is safer and more defensible.

## GitHub Competitor Leads

GitHub search for candidate ranking / ATS scoring / resume-JD matching mostly returned small
Streamlit, Flask, or LLM-wrapper tools. That is good for competitive positioning: most public repos
do not show deterministic 100K-scale ranking, golden hash reproduction, test gates, or detailed
audits.

But public GitHub does show what judges may expect visually:

- upload JD + resumes;
- fit score;
- skill gaps;
- explanation;
- PDF/CSV export;
- dashboard/API demo.

Your repo is stronger on reproducibility and tests. It is still thinner on a polished recruiter
workflow than a product-first entry could be.

## Research / SOTA Leads

Sources:

- ConFit: https://arxiv.org/abs/2401.16349
- ConFit v2: https://arxiv.org/abs/2502.12361
- ConFit v3: https://arxiv.org/abs/2605.09760
- Category-aware MoE + LLM augmentation for person-job fit: https://arxiv.org/abs/2604.21264
- Long-context ranking with calibrated LLM distillation for person-job fit: https://arxiv.org/abs/2601.10321
- LLM hiring pitfalls: https://arxiv.org/abs/2507.02087

What these papers imply:

- Best systems are at least two-stage: retrieve broadly, rerank carefully.
- Hard negatives matter because near-fit candidates are where ranking quality is won.
- Long resume/JD matching is not solved by naive cosine similarity.
- LLM reranking improves controllability/explainability but creates cost, reproducibility, and bias risks.
- Hiring evaluation must show validity and job-relatedness, not just pretty summaries.

For this repo, the implication is not “throw away BM25.” The implication is:

- keep deterministic BM25/features for the official 100K path;
- add external and blind evals that prove the handcrafted features beat shallow baselines;
- build role-family adapters for backend/devops/data if generality is part of the story;
- never let an untested cross-encoder wreck the frozen golden artifact.

## Why Backend / DevOps / Data Still Lose To Keyword

This is not mysterious.

The current scoring DNA is Senior AI/Search/Relevance:

- ranking/retrieval/recommender evidence is heavily rewarded;
- AI/ML production evidence is treated as central;
- product-company and search-eval signals carry weight;
- backend/devops/data terms are present, but secondary.

The transfer proxy labels for backend/devops/data reward broader role-family terminology:

- Backend wants APIs, services, distributed systems, databases, language/runtime depth.
- DevOps wants cloud, Kubernetes, Terraform, CI/CD, observability, SRE signals.
- BI wants SQL, dashboards, ETL, warehouse, reporting and stakeholder analytics.

A keyword baseline wins those roles because the proxy labels are closer to direct keyword coverage
than to nuanced AI-search fit. This is not fatal for Track 1 if the official JD is Senior AI Engineer.
It is fatal for a “dominant across every Redrob product” claim unless role adapters are added and
validated.

## Real 95+ Path

The web-data path that actually moves the score:

1. Build a multi-source external eval pack:
   `cnamuangtoun`, `0xnbk`, duplicate-checked `layan009/facehuggerapoorv`, one synthetic accept/reject dataset, and one job-query dataset.

2. Build a blinded challenge-pool judge pack:
   fresh candidates from the actual pool, selected after freeze, judged without exposing rank/source system, with multiple judges and disagreement analysis.

3. Add role-family adapters:
   preserve the golden Senior AI run, but make backend/devops/data demos compile into genuinely different feature weights and explanations.

4. Improve product demo breadth:
   Redrob OS mode: recruiter query -> compiled JD -> ranked shortlist -> evidence -> CSV/API export -> audit/fraud flags.

5. Keep the official path frozen unless a lab challenger beats it on:
   hidden-proxy eval, external eval, runtime, tests, golden reproducibility, and reasoning quality.

## Bottom Line

Scraping harder is not the missing ingredient. Blind, independent labels are.

Public research can make the repo look much more serious, and it can expose exactly where the
system is weak. It cannot make social threads or scraped announcements substitute for judged
candidate relevance.
