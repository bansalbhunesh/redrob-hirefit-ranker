# Feature JD Traceability

This ranker uses deterministic features because the official run must score 100K candidates offline on CPU. Each feature group maps to a JD or challenge requirement.

## Technical Fit

- `core_skill_match`: embeddings, retrieval, vector DBs, LLM production, Python ML, and evaluation terms required by the Senior AI Engineer JD.
- `nice_skill_match`: LoRA/fine-tuning, learning-to-rank, distributed systems, HR-tech/marketplace exposure, and open-source signals.
- `skill_depth_score`: duration, proficiency, and endorsements so keyword lists do not outrank lived experience.
- `assessment_score_avg`: platform-validated competence from Redrob assessments.
- `github_signal` and `open_source_signal`: coding credibility and public AI/ML contribution evidence.

## Career Evidence

- `ir_ranking_experience`: career-history evidence for search, retrieval, ranking, recommender, and relevance work.
- `production_evidence`: shipped/deployed/live/latency/scale evidence, because the JD asks for builders, not only researchers.
- `product_company_ratio`: product-company context preferred by the JD.
- `consulting_only_flag`: tracks the JD concern about consulting-only backgrounds, softened when production evidence is strong.
- `senior_title_held`, `career_trajectory_score`, `yoe_fit_score`, `ml_ai_tenure_score`: seniority and recent hands-on fit.

## Hireability

- `availability_score`: last-active and open-to-work signals.
- `responsiveness_score`: recruiter response rate and response time.
- `interview_reliability`: completion rate as a professionalism signal.
- `engagement_score`: views, applications, saves, and search appearances.
- `profile_quality`: completeness plus verified contact/account signals.
- `notice_period_score`: India-aware notice-period handling; 90 days is treated as standard, not a disqualifier.
- `location_score` and `relocation_willing`: Pune/Noida/India logistics fit.

## Guardrails

Hard honeypots are absolute exclusions from scoring:

- claimed YOE contradicts career duration
- expert core skills with zero duration
- multiple current jobs
- salary inversion
- impossible education timeline
- title-description contradictions
- endorsement inflation on incomplete profiles
- impossible notice period

Soft disqualifiers compound through multipliers: consulting-only without production evidence, pure research without deployment, CV/speech/robotics-primary mismatch, keyword stuffing, and title hopping.
