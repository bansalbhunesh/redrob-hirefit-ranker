# RESEARCH.md

Research date: 2026-06-12 IST  
Project under audit: `bansalbhunesh/redrob-hirefit-ranker`  
Hackathon: India Runs Track 1, Redrob AI x Hack2skill, Track 1 submission deadline: 2026-06-28

## Executive Ground Truth

The winning bar for India Runs Track 1 is not a generic resume keyword matcher. The official challenge asks for an AI candidate discovery/ranking system that:

- deeply interprets nuanced job descriptions;
- ranks candidates by semantic and contextual fit, not surface keywords;
- integrates profile attributes, career metadata, and activity/behavioral signals;
- returns a fast, accurate, predefined-format ranked shortlist;
- ships a well-organized GitHub repo, clear architecture/methodology documentation, and reproducible results.

The strongest possible submission should look like a compressed production talent intelligence system: hybrid retrieval, learned/validated reranking, transparent scoring evidence, fairness/validity checks, adversarial resume robustness, calibrated output, and a demo that makes Redrob believe the work could plug into their roadmap.

My inferred champion target:

- Ranking quality: beats TF-IDF/BM25/raw embedding baselines on the provided dataset, with nDCG@10 / Recall@K / MAP reported. If labels are sparse or hidden, it should still provide a reproducible evaluation harness, public benchmark validation, ablations, and sanity/reasoning tests.
- System quality: deterministic Docker run, pinned dependencies, no required private API for the official output, CI passing, documented assumptions, and a one-command reproduction path.
- Product quality: recruiter-facing ranked shortlist with reasons, critical gap flags, confidence/calibration, ability to audit why candidate A outranks candidate B, and data export in the required format.
- Sponsor fit: explicit alignment with Redrob's India-first AI operating system: multilingual handling, scale, low-latency/cost consciousness, ATS/CRM integration story, fraud/prompt-injection defense, and candidate/recruiter trust.

## Official India Runs Track 1 Requirements

Source: Hack2skill event page  
https://hack2skill.com/event/india_runs/

Official Track 1 framing:

- Track 1 is "The Data & AI Challenge" / "Intelligent Candidate Discovery."
- Target participants include AI/ML engineers, data scientists, developers, search/retrieval specialists, and LLM practitioners.
- Mission: build a robust proof of concept that ranks candidates, not merely filters.
- Expected system capabilities: deep job understanding, contextual relevance, signal integration, and fast accurate ranked shortlists.
- Required submission: complete code in GitHub, clear documentation/README, and ranked output file in predefined format.
- Timeline: registrations and Track 1 submissions opened 2026-05-19; Track 1 submission closes 2026-06-28; evaluation begins 2026-07-03 and closes 2026-07-16; virtual finale is 2026-07-22.
- Judges are drawn from Redrob leadership, AI researchers, founders from Indian product companies, and senior engineers in Redrob's partner ecosystem.

Source: Hack2skill India Runs career page  
https://hack2skill.com/event/india_runs/career/

Important sponsor implications:

- India Runs submissions are also work samples seen by the Redrob team.
- Track 1 is described as the exact problem Redrob is solving.
- Redrob highlights 790M+ professional profiles, 20M+ live jobs, 30+ supported languages, and products around Hire, Discover, Signal, AI Apps, Career, and Redrob OS.
- Redrob's hiring page emphasizes Senior AI/ML work involving LLM systems, RAG pipelines, fine-tuning, inference optimization, GPU fleet management, and scale.

Hack2skill precedent:

- Prior Hack2skill technical hackathons used judging criteria such as code reproducibility/testing, model training/inference, technical implementation, preprocessing/EDA, documentation, creativity/originality, scalability, prototype quality, usability, and impact.
- Sources:
  - Intel oneAPI GenAI Hackathon: https://hack2skill.com/hack/oneapi-genai-hackathon/
  - Intel oneAPI Hackathon 2023: https://hack2skill.com/intel-oneapi-hackathon-2023/
  - ICC/Nium NEXT IN writeup: https://blog.hack2skill.com/icc-nium-next-in-hackathon

Inference: even if India Runs does not publish a numeric rubric, the judging surface is almost certainly repo quality + technical depth + measurable results + originality + usability + sponsor relevance.

## What Redrob Actually Cares About

Sources:

- Redrob homepage: https://redrob.io/
- Redrob Resume Ranker: https://redrob.io/resume-ranker
- Redrob People Search: https://redrob.io/people-search
- Redrob Job Search: https://redrob.io/job-search
- Redrob Company Search: https://redrob.io/company-search
- Redrob India-first LLM article: https://redrob.io/newsroom/affordable-ai-built-in-india-first-redrob-ceo-felix-kim-indian-vcs

Redrob positioning:

- "Next billion professionals," 700M+/790M+ profiles, 30+ languages, real data for hiring/sales/jobs/research.
- Hiring and talent products focus on people search, job search, company intelligence, and resume ranking.
- Resume Ranker promise: score and rank resumes against job criteria, evaluate skills, experience depth, role relevance, compare applicants side by side, export clean shortlists, and make team decisions more objective.
- People Search promise: natural-language search across profiles, intent parsing, company signals, tenure filters, seniority classifiers, verified contacts, and CRM export.
- Job Search promise: skills-first ranking, match scores, real-time job alerts, multilingual search in Indian languages.
- Company Search promise: firmographics, tech stack, hiring signals, leadership mapping, growth signals, and company-to-contact workflows.
- Redrob's India-first technical thesis emphasizes affordable LLM infrastructure, local-language token costs, LoRA-adapted open models, AWS Bedrock, on-device inference for smaller models, and application-layer revenue in HR/GTM.

What would make a Redrob judge say "this is exactly what we need":

- Uses the challenge data as a miniature version of Redrob's people/job graph rather than as flat CSV rows.
- Demonstrates semantic, multilingual, intent-aware job understanding.
- Extracts structured features Redrob can actually productize: skill recency, seniority fit, title trajectory, company/industry match, location/availability, education/certification requirements, activity/behavioral proof, and disqualifier handling.
- Explains every rank in recruiter language, not only model math.
- Has a deployment and integration story: API endpoint, batch inference, Docker, output artifact, latency measurement, and eventual Greenhouse/Lever/ATS export pattern.
- Handles trust: fairness tests, opt-out/manual-review category, prompt-injection/hidden-text defense, PII handling, and no auto-rejection framing.

## What Strong Hackathon Winners Look Like

Sources:

- Hack2skill Gen AI Exchange 2025 finale: https://blog.hack2skill.com/gen-ai-exchange-hackathon-finale
- Build Fest 2025 winners: https://blog.hack2skill.com/spotlight-on-innovation-meet-the-winners-of-build-fest-25
- AI for Impact APAC: https://blog.hack2skill.com/ai-for-impact-empowering-change-with-ai

Pattern across Hack2skill/Google-style winners:

- Winners solve real-world workflows, not toy demos.
- Strong projects combine working product, domain specificity, explainability, and deployment readiness.
- Winning writeups consistently emphasize originality, scalability, impact, polished prototype/demo, and use of the sponsor's technology or domain priorities.

Examples:

- Gen AI Exchange 2025 saw 2.7 lakh+ developers, 4,457 prototypes, and top 100 finalist teams. Winners included agentic artisan marketplace tooling, RAG legal analysis, explainable misinformation detection, career guidance with skill-gap detection, Jira-integrated test automation, and AI governance dashboards.
- Build Fest winners used Gemini + FlutterFlow to ship real-time misinformation detection, localized farm advisory, and patient-friendly health summaries.
- AI for Impact APAC selected finalists after prototype rounds and judged polished prototypes on innovation, feasibility, and social impact.

Inference for this submission: a winning Track 1 repo cannot merely output a leaderboard. It needs to make the judge feel the team understood recruiting as a workflow, not just a scoring task.

## Prior AI Recruiting Hackathon Bar

Sources:

- RecruiterX, xAI Hackathon 2025: https://devpost.com/software/recruiterx
- Sentinel, xAI Hackathon 2025: https://devpost.com/software/sentinel-iu5k4g
- betterATS: https://devpost.com/software/better-ats
- Verify: https://devpost.com/software/verify-27gui6
- SmartHire: https://devpost.com/software/smarthire-h16ksx

Strong public hackathon implementations go beyond resume/JD cosine similarity:

- RecruiterX uses X activity as a talent signal, an 8-dimensional scoring model, anti-noise filters, peer-recognition graph signals, proof-of-work indicators, Greenhouse export, autonomous outreach, and a planned feedback/calibration loop.
- Sentinel builds end-to-end technical hiring: organic candidate discovery from X, GitHub enrichment, resume-based personalized assessments, real-time code execution, behavioral/keystroke analytics, adaptive challenge questions, code + communication scoring, and detailed hiring reports.
- Verify cross-references resume claims against GitHub repositories, uses vector search and SentenceTransformers, structured Pydantic outputs, and Gemini-based code analysis.
- betterATS adds contextual resume analysis, standardized profiles, and video responses.
- SmartHire is closer to the commodity baseline: upload resume + JD, parse files, prompt Gemini, return strengths/weaknesses/recommendations.

Champion implication: if this repo looks like SmartHire, it is average. If it looks closer to RecruiterX/Sentinel in signal richness, workflow depth, and calibration, it can compete.

## Public GitHub Implementations

Sources:

- AI-Powered Talent Intelligence System: https://github.com/Shivanikanodia/AI-Powered-Talent-Intelligence-System
- job-resume-matching-algo: https://github.com/ruozhengu/job-resume-matching-algo
- bias-in-llm-ranking: https://github.com/zinia94/bias-in-llm-ranking
- WorkRB benchmark: https://github.com/techwolf-ai/workrb
- AI-Screener: https://github.com/mohsinraza2999/AI-Screener

Public implementation patterns:

- Commodity repos: TF-IDF / cosine / SentenceTransformer similarity, simple skill matching, Streamlit/FastAPI, top-10 output. These are easy to reproduce and easy to beat.
- Better repos: hybrid retrieval, cross-encoder reranking, evidence-grounded LLM summaries, structured feature scoring, recruiter UI, Docker, tests, CI, and explainability.
- Stronger research-grade repos measure NDCG, MAP, MRR, Recall@K, fairness, consistency, order bias, and reranking robustness.
- The WorkRB benchmark is important because it demonstrates the right benchmark discipline: ranking artifacts should be replayable, versioned, schema-validated, and evaluated with MAP/MRR/nDCG@k/Recall@k/hit@k/R-Precision.

Champion implication: the submission should include both the ranker and the evaluator. A ranked CSV without an evaluator is not enough.

## Research SOTA

### ConFit

Source: https://arxiv.org/html/2401.16349v1

Key facts:

- ConFit frames resume-job matching as dense retrieval with contrastive learning and augmentation.
- It addresses sparse interaction labels and ranks tens of thousands of resumes/jobs with FAISS-scale retrieval.
- It reports MAP and nDCG@10 against BM25, TF-IDF, XGBoost, DPGNN, InEXIT, RawEmbed, and OpenAI embeddings.
- It beats prior methods by up to about 20-30 absolute points in ranking tasks depending on task/dataset.

Technical bar:

- Public champion should at least know BM25 is a hard baseline, not a strawman.
- Dense retrieval needs hard negatives or other rank-specific training, not just off-the-shelf embeddings.

### ConFit v2

Source: https://arxiv.org/html/2502.12361v1

Key facts:

- ConFit v2 adds Hypothetical Resume Embedding (HyRe) and Runner-Up Mining (RUM).
- It reports average absolute improvement over ConFit of about 13.8% recall and 17.5% nDCG; in main results, about 17.1% recall and 20.4% nDCG with E5-base.
- It evaluates on AliYun and Intellipro datasets and uses E5/Jina encoders, GPT-4o-mini for hypothetical resumes, contrastive training, hard negatives, and FAISS.
- It notes fewer than 0.05% of total possible resume/job pairs are annotated, which is exactly the sparse-label problem hackathon rankers must acknowledge.

Technical bar:

- A champion solution has at least a two-stage system: candidate generation and reranking.
- It has some version of hard-negative reasoning: near-miss candidates, non-negotiable gates, or contrastive separation.

### ConFit v3

Source: https://arxiv.org/html/2605.09760v1

Key facts:

- ConFit v3 adds LLM-based reranking on top of retrieval to improve controllability and explainability.
- It studies multi-pass sliding-window reranking, listwise RL objectives, noisy sample removal, SFT distillation, and Qwen3-8B/32B rerankers.
- It reports ConFit v3 beating ConFit v2 and strong LLM prompt baselines such as GPT-5 and Claude Opus 4.5 on person-job fit reranking.
- It emphasizes person-job fit is unlike generic retrieval because resumes/jobs are long and labels are sparse/noisy.

Technical bar:

- For a hackathon, full RL fine-tuning is likely too much, but a champion can approximate the architecture: retrieve top N cheaply, then LLM/listwise rerank top K with structured reasoning, pairwise sanity checks, and deterministic fallback.

### Validity and Fairness

Sources:

- Measuring Validity in LLM-based Resume Screening: https://arxiv.org/html/2602.18550v1
- JobFair: https://arxiv.org/html/2406.15484v2
- AI Hiring with LLMs multi-agent framework: https://arxiv.org/html/2504.02870v1

Key facts:

- Resume screening needs validity, not just fairness. A model must prefer candidates with more job-relevant qualifications and avoid preferring equally qualified candidates based on irrelevant attributes.
- JobFair uses counterfactual resumes and statistical tests to separate bias types.
- Multi-agent/RAG frameworks argue against monolithic "one prompt scores everything"; modular extraction, evaluation, summary, and score formatting improves traceability and adaptability.

Technical bar:

- Champion repo includes counterfactual fairness/robustness tests: name/gender proxies, order sensitivity, AI-generated resume phrasing, hidden text/prompt injection, missing fields, and equally-qualified candidate ties.
- It marks "needs manual review" rather than pretending a model should decide everything.

## Production HR AI Systems

Sources:

- Eightfold technical blog: https://eightfold.ai/engineering-blog/ai-powered-talent-matching-the-tech-behind-smarter-and-fairer-hiring/
- hireEZ Applicant Review: https://hireez.com/applicant-review/
- hireEZ ResumeSense: https://hireez.com/newsroom/hireez-launches-resumesense/
- Greenhouse AI features: https://support.greenhouse.io/hc/en-us/articles/33043749845403-Greenhouse-AI-features
- Greenhouse Talent Matching: https://support.greenhouse.io/hc/en-us/articles/41396009937307-Talent-Matching
- Greenhouse Talent Matching FAQ: https://support.greenhouse.io/hc/en-us/articles/41131886674075-Talent-Matching-FAQ
- Greenhouse Real Talent: https://www.greenhouse.com/real-talent-candidate-matching
- Lever: https://www.lever.co/

Production patterns:

- Eightfold blends semantic embeddings with interpretable structured features: skill overlap, recent skill usage, title progression, seniority fit, industry/company similarity, ideal-candidate signals, hiring-manager context, and calibrated prediction from historical outcomes.
- Greenhouse Talent Matching is assistive AI. Recruiters define weighted calibration criteria, candidates are grouped into match categories, protected attributes/proxies are blocked or warned, opt-out/manual review flows exist, and AI does not auto-advance/reject.
- Greenhouse Real Talent adds fraud detection and identity verification around matching.
- hireEZ Applicant Review emphasizes transparent job-fit explanations, ATS integration, recruiter feedback, and no outside-profile enrichment for inbound applicant review.
- hireEZ ResumeSense detects hidden text, prompt injection, unusual match patterns, and AI-manipulated resumes; internal tests found 3-5% of resumes contained hidden or misleading content.
- Lever positions itself as ATS+CRM with AI embedded across screening, interviewing, reporting, and next-best actions.

Champion implication:

- Production systems do not stop at a numerical score. They include calibration, categories, explanations, manual override, compliance posture, fraud protection, and feedback loops.

## Reddit / Practitioner Signal

Sources:

- r/recruitinghell AI resume screening discussion: https://www.reddit.com/r/recruitinghell/comments/1gvcpz4/ai_resume_screening_should_be_illegal/
- r/cscareerquestions AI filters discussion: https://www.reddit.com/r/cscareerquestions/comments/1kt12kw/whats_the_best_way_to_get_through_ai_job_filters/
- r/datascience job-hunt feedback: https://www.reddit.com/r/datascience/comments/1hyploh/200_applications_no_response_please_help_i_have/
- r/MachineLearning HireVue discussion: https://www.reddit.com/r/MachineLearning/comments/cmihda/d_company_hirevue_provides_ai_for_earlystage/
- r/recruitinghell AI-generated resumes discussion: https://www.reddit.com/r/recruitinghell/comments/1lk9uty/employers_are_buried_in_aigenerated_r%C3%A9sum%C3%A9s/

Signal, treated cautiously because Reddit is anecdotal:

- Candidates distrust AI screening because ATS parsing is unreliable, candidates feel filtered before a human sees them, and opaque rejection reasons create resentment.
- Recruiter/practitioner discussions repeatedly emphasize tailoring to the role, not listing everything.
- ML practitioners distrust vague AI interview/video scoring claims, especially affect/eye-contact signals.
- A real-world ranker must be transparent, parse-robust, and respectful of human oversight.

Champion implication:

- A winning system should show restraint: it should not claim to "eliminate bias" or "decide hire/no-hire." It should show evidence, uncertainty, manual review, and auditability.

## What The Champion Submission Does

### Data Understanding

- Loads all challenge files with schema validation.
- Documents every field and missingness pattern.
- Identifies judge families / query groups / role types if the dataset has them.
- Normalizes skills, titles, company names, location, education, years, dates, salary/notice if present.
- Detects language and supports Hinglish/Indian regional terms where possible.
- Separates hard requirements, preferred requirements, responsibilities, seniority, domain, and disqualifiers from the job description.

### Ranking Architecture

Minimum champion architecture:

1. Candidate generation:
   - BM25/lexical retrieval for exact skills and rare terms.
   - Dense retrieval with multilingual embeddings.
   - Optional graph/metadata filters for required fields.
   - FAISS or equivalent for scale.

2. Structured feature layer:
   - Skill exact/semantic match.
   - Recency of skills.
   - Years/depth of experience.
   - Seniority/title trajectory.
   - Domain/company/industry similarity.
   - Education/certifications if job-relevant.
   - Location/availability/notice constraints if present.
   - Activity/behavioral proof signals if the dataset includes them.
   - Missing-critical-signal penalties.

3. Reranking:
   - Cross-encoder or LLM listwise reranker for top K.
   - Hard negative handling for near-miss candidates.
   - Calibration of final score into categories: Strong / Good / Partial / Limited / Manual Review.
   - Deterministic fallback if LLM/API unavailable.

4. Explanation:
   - Per-candidate evidence snippets.
   - Reason codes, matched/missing skills, seniority/domain evidence.
   - "Why above/below" comparison for adjacent ranked candidates.
   - Explicit uncertainty/manual review triggers.

5. Safety:
   - Prompt-injection and hidden-text stripping from resumes.
   - PII minimization.
   - Counterfactual fairness checks.
   - Order-bias tests.
   - No auto-reject framing.

### Evaluation

Champion reports:

- NDCG@K, MAP, MRR, Recall@K and per-query/per-family breakdowns.
- Baselines: random, TF-IDF, BM25, raw embeddings, hybrid BM25+dense, LLM-only, final model.
- Ablations: without structured features, without reranker, without calibration, without hard negatives.
- Robustness: shuffled candidate order, name/gender swaps, hidden prompt text, AI-generated resume variants, missing fields.
- Latency/cost: batch runtime, per-query runtime, memory, model/API cost if any.
- Reproducibility: replayable ranking artifacts and versioned outputs.

Reasonable champion metric expectation:

- On public ConFit-like benchmarks, a modern two-stage system should be in the range of ConFit v2/v3, not raw embeddings.
- On the hackathon dataset, if labels are hidden, champion should still show that its final model beats baselines on any available validation/evaluation proxy and produces judge-ready output deterministically.

### Demo / Presentation

Champion demo:

- Starts with a recruiter's query/JD.
- Shows top candidates with match categories and concise evidence.
- Shows why the winner is above the runner-up.
- Shows manual-review and fraud/prompt-injection safeguards.
- Shows CSV output format.
- Shows a one-command Docker reproduction and a brief architecture diagram.
- Uses Redrob language: India-scale, multilingual, real data, candidate discovery, work sample, trust, speed.

## Champion Scorecard For This Hackathon

This is the standard I will use in `GAPS.md`.

| Dimension | Champion Bar |
|---|---|
| Technical depth | Multi-stage retrieval + reranking + structured features + calibration + explainability |
| ML rigor | Baselines, metrics, ablations, held-out eval, rank metrics, robustness tests |
| Result quality | High NDCG/Recall versus BM25/dense baselines, sensible top-5 evidence |
| Reproduction safety | Docker, pinned deps, CI/tests, deterministic outputs, no hidden API dependency |
| Demo quality | Recruiter workflow, evidence, comparison, export, fast happy path |
| Presentation | Clear README, architecture, methodology, results table, limitations, roadmap |
| Sponsor alignment | Redrob OS/product language, multilingual/India-scale/ATS story, Redrob-specific priorities |
| Generalizability | Works across roles/families/languages; handles missing/noisy data |
| Reasoning quality | Evidence-grounded explanations, not vague LLM prose |
| Deployment story | API/batch mode, latency/cost, observability, security/privacy/compliance stance |

## Bottom Line

The champion submission is not "a ranker." It is a recruiter trust machine:

- fast enough to scale,
- accurate enough to beat baselines,
- explainable enough for humans to trust,
- auditable enough for high-stakes hiring,
- aligned enough that Redrob can imagine integration.

Any repo missing evaluation, baselines, reranking, evidence-grounded explanations, reproducibility, and sponsor-specific trust/safety is not competing with the champion. It is competing for a participation-tier award.
