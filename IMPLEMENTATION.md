# Implementation Notes

## Methodology

The released JD is not a generic AI role. It asks for a Senior AI Engineer who has shipped production retrieval, ranking, matching, and evaluation systems at product speed. The ranker treats skills as supporting evidence, not the primary source of truth.

Plan D v2 pipeline:

1. Parse candidates with `orjson` when available.
2. Render structured candidate text from profile, career, skills, education, logistics, and Redrob signals.
3. Render deterministic semantic concept markers and phrase tokens for plain-language retrieval, RAG, vector, recommender, and evaluation evidence.
4. Compute BM25 lexical scores using `bm25s.get_scores()` when installed, otherwise `rank-bm25`.
5. Extract a deterministic 28-feature matrix for every loaded candidate.
6. Compute `base_score` from technical/career/logistics/BM25 features.
7. Apply `base_score * behavioral_multiplier * honeypot_multiplier * disqualifier_multiplier`.
8. Sort deterministically and output exactly 100 grounded rows.

No hosted LLM re-ranking or candidate API scoring is used.

## Feature Matrix

Skills:

- `core_skill_match`, `nice_skill_match`, `skill_depth_score`, `endorsement_trust`, `assessment_score_avg`, `disqualifier_skill_flag`, `keyword_stuffer_flag`, `github_signal`

Career:

- `product_company_ratio`, `consulting_only_flag`, `ir_ranking_experience`, `production_evidence`, `senior_title_held`, `career_trajectory_score`, `scale_signal`, `code_writing_recent`

Experience:

- `yoe_fit_score`, `education_score`, `ml_ai_tenure_score`, `open_source_signal`

Behavioral:

- `availability_score`, `engagement_score`, `responsiveness_score`, `interview_reliability`, `profile_quality`, `notice_period_score`

Logistics:

- `location_score`, `relocation_willing`

## Multipliers

- `behavioral_multiplier`: combines open-to-work, recency, response quality, profile quality, interview reliability, recruiter saves, GitHub activity, assessments, verification, and notice period.
- `honeypot_multiplier`: `0.0` only for hard traps such as expert-zero-duration core skills, multiple current jobs, impossible education, impossible timeline math, or contradictory profiles.
- `disqualifier_multiplier`: compounds consulting-only, pure-research, CV/speech/robotics-primary, keyword-stuffer, title-hopper, salary-inversion, and endorsement-inflation penalties.

The CLI prints total hard honeypots detected and hard honeypots in the emitted output.

`--profile-memory` is available only with `--max-candidates <= 5000`; Python `tracemalloc`
is too slow for the official 100K reproduction path. For full-run wall-clock and
RSS profiling, use `scripts/measure_runtime_memory.py`.

## Runtime

The official path scores every loaded candidate:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

`--candidate-pool N` exists for demos/profiling only. The submission path should leave it at `0`.

On the local 100K challenge file, the preferred `bm25s` backend generated the validated top-100 `submission.csv` in an observed 123-184 seconds across repeated runs. The run loaded and scored all 100,000 candidates, detected 53 hard honeypots, and emitted 0 hard honeypots in the top 100. A profiled full run measured peak RSS at 4.33 GB across the parent plus worker processes.

Feature scoring is parallelized across CPU worker processes by default, capped at 8 workers for memory safety. `--workers 1` remains the serial escape hatch and produces byte-identical output.

The local silver-label harness (`scripts/build_silver_labels.py` and `scripts/evaluate_silver.py`) is for development and defense only. On the first 20K candidates, the latest validated ranker scored NDCG@10 0.9088, NDCG@50 0.8482, P@10 1.0000, and MAP 0.7518 against heuristic JD-rule labels.

The FastAPI/dashboard payload is generated from `CandidateFeatures` directly, exposing feature values, behavioral/honeypot/disqualifier multipliers, and feature-derived flags. It does not infer honeypots by searching reasoning text.

## Validation

```bash
python -m pytest -q
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
python scripts/validate_submission.py ./submission.csv
# Also run the official challenge validator from the downloaded bundle when available.
```
