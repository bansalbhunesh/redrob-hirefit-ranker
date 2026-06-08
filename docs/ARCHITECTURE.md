# Redrob HireFit Ranker Architecture

## Goal

Rank the top 100 candidates for the Redrob Senior AI Engineer JD while satisfying the official constraints:

- CPU-only execution.
- No network or hosted LLM/API scoring during ranking.
- Deterministic output.
- Full 100K reproduction in under 5 minutes.
- Validator-safe CSV output.

The final measured local run used `bm25s`, scored all 100,000 candidates, and completed in **219.1 seconds** with zero hard honeypots in the emitted top 100.

## System Overview

```mermaid
flowchart LR
    A["candidates.jsonl"] --> B["orjson parser"]
    B --> C["structured text renderer"]
    C --> D["phrase and concept expansion"]
    D --> E["BM25 score: bm25s preferred"]
    B --> F["28-feature extractor"]
    E --> G["weighted base score"]
    F --> G
    F --> H["behavioral multiplier"]
    F --> I["honeypot multiplier"]
    F --> J["disqualifier multiplier"]
    G --> K["final score"]
    H --> K
    I --> K
    J --> K
    K --> L["sort by score, then candidate_id"]
    L --> M["top-100 grounded reasoning"]
    M --> N["submission.csv"]
```

## Why Not Hosted LLM Or Dense Embeddings?

Research supports a best-relevance pattern of retrieve, dense rerank, and cross-encoder/LLM review. That is excellent when latency, cost, and network access are available.

For this official path, those trade-offs are risky:

- Hosted LLM/API scoring breaks offline reproducibility.
- Local dense embedding generation can push CPU-only 100K runs beyond the 300-second limit.
- Black-box scoring makes Stage 3/4 review harder to defend.

The official ranker therefore uses deterministic sparse expansion plus feature scoring. Dense embeddings are documented as a future improvement, not a dependency.

## Retrieval Layer

The retrieval layer renders weighted structured text from:

- current title, headline, summary, location, and industry
- career titles, companies, industries, descriptions, and durations
- skill names, proficiency, endorsements, and duration
- education fields
- Redrob availability and platform signals

It then adds deterministic semantic concept markers for safe sparse recall:

- retrieval/search systems
- vector databases and ANN search
- RAG and agentic systems
- recommender/matching systems
- ranking/evaluation metrics

`bm25s` is preferred for speed; `rank-bm25` remains a fallback. BM25 is only one feature in the final score, not the final judge.

## 28-Feature Recruiter Matrix

The feature extractor produces stable values in `[0, 1]` for:

Skills:

- `core_skill_match`
- `nice_skill_match`
- `skill_depth_score`
- `endorsement_trust`
- `assessment_score_avg`
- `disqualifier_skill_flag`
- `keyword_stuffer_flag`
- `github_signal`

Career:

- `product_company_ratio`
- `consulting_only_flag`
- `ir_ranking_experience`
- `production_evidence`
- `senior_title_held`
- `career_trajectory_score`
- `scale_signal`
- `code_writing_recent`

Experience:

- `yoe_fit_score`
- `education_score`
- `ml_ai_tenure_score`
- `open_source_signal`

Behavioral:

- `availability_score`
- `engagement_score`
- `responsiveness_score`
- `interview_reliability`
- `profile_quality`
- `notice_period_score`

Logistics:

- `location_score`
- `relocation_willing`

## Scoring

```text
base_score = weighted(
  bm25_score,
  technical skills,
  production/retrieval evidence,
  product-company evidence,
  seniority,
  experience,
  logistics
)

final_score = base_score
            * behavioral_multiplier
            * honeypot_multiplier
            * disqualifier_multiplier
```

The model intentionally uses multipliers rather than only additive penalties. This mirrors recruiter reality: a strong technical profile can still be unusable if it is stale, unreachable, contradictory, or impossible.

## Guardrails

Hard honeypots receive `honeypot_multiplier = 0.0`:

- salary minimum greater than maximum
- expert core skills with zero duration
- multiple current jobs
- impossible education timeline
- career timeline inconsistent with claimed experience
- too-short career history for claimed YOE
- title/description contradiction
- endorsement inflation with low profile quality
- impossible notice period

Soft disqualifiers compound through `disqualifier_multiplier`:

- consulting-only career
- pure research without deployment evidence
- CV/speech/robotics-primary mismatch
- AI keyword stuffing without career support
- title hopping

The consulting-only penalty is softened when the candidate has strong production evidence, because Indian services companies can still contain strong product/platform builders.

## Reasoning

Reasoning is deterministic and grounded:

- It mentions only facts present in the candidate JSON or feature values.
- Top ranks emphasize JD-aligned strengths.
- Lower ranks include honest concern tone.
- Candidate ID controls deterministic wording variation so output is reproducible without identical templates.

The dashboard uses `CandidateFeatures` directly for flags, multipliers, and honeypot reasons. It does not infer guardrails by searching the reasoning text.

## Validation

Verified gates:

```bash
python -m compileall -q src tests rank.py apps scripts
python -m pytest -q
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --bm25-backend bm25s
python scripts/validate_submission.py submission.csv
python validate_submission.py submission.csv
```

Final measured output:

```text
Runtime: 219.1s
Loaded candidates: 100000
Ranked pool: 100000
Rows emitted: 100
BM25 backend: bm25s
Hard honeypots detected: 23247
Hard honeypots in output: 0
```
