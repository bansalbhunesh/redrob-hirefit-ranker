# Redrob Candidate Ranker Architecture

## 1. Goal

Rank the top 100 candidates for the Redrob **Senior AI Engineer - Founding Team** JD while satisfying CPU-only, no-network, no-GPU, sub-5-minute reproduction constraints.

Final V6 measurement in the pinned python:3.11 image: all 100,000 candidates rank in
**136.0 s pipeline / 149.1 s wall** at 2 CPU / 16 GiB, with sampled peak memory
**4.13 GiB**; 53 honeypots are detected and 0 enter the top 100. The exact input,
model, environment, backend, counts, integrity totals and output hash are verified
before atomic publication (full history: `docs/runtime_matrix.md`).

## 2. Pipeline

```mermaid
flowchart LR
    A["candidates.jsonl"] --> B["Parser"]
    B --> C["Structured Text Renderer"]
    C --> D["BM25 Scorer: bm25s preferred, rank-bm25 fallback"]
    B --> E["33-Feature Deterministic Extractor"]
    D --> F["Base Score"]
    E --> F
    E --> G["Behavioral / Honeypot / Disqualifier Multipliers"]
    F --> H["Final Score"]
    G --> H
    H --> I["Deterministic Top 100"]
    I --> J["Grounded Reasoning"]
    J --> K["submission.csv"]
    K --> L["Official Validator"]
```

## 3. Core Design

- BM25 is a compact lexical signal, not the final judge.
- The 33-feature matrix encodes JD intent: production retrieval/ranking, product-company history, Python/evaluation, seniority, role-family depth, location, availability, and trap avoidance.
- Multipliers enforce recruiter reality: a technically strong but unreachable or impossible profile should fall sharply.
- Reasoning is generated from actual profile fields and feature triggers only.

## 4. Scoring

```text
base_score = weighted(BM25 + skill + career + experience + logistics features)
final_score = base_score
            * behavioral_multiplier
            * honeypot_multiplier
            * disqualifier_multiplier
```

Hard honeypot traps receive `honeypot_multiplier = 0.0`. Softer JD disqualifiers compound through `disqualifier_multiplier`.

## 5. Guardrails

The detector penalizes:

- Salary min > max.
- Expert core skill with zero duration.
- Multiple current jobs.
- Impossible education timeline.
- Career timeline inconsistency.
- Endorsement inflation with low profile completeness.
- Non-target title with heavy AI/retrieval descriptions.
- Consulting-only, pure-research, CV/speech/robotics-primary, keyword-stuffed, or title-hopping profiles.

## 6. Reproducibility

Official command:

```bash
PYTHONHASHSEED=0 python rank.py --release --candidates ./candidates.jsonl \
  --out ./submission.csv --workers 2
```

No hosted LLM/API calls are made during ranking. General runs may fall back to
`rank-bm25`, but the official V6 `--release` path requires `bm25s` and fails closed.

Feature scoring is parallelized across CPU workers by default, capped at 8 workers for memory safety. `--workers 1` remains the serial escape hatch and produces byte-identical output.

The FastAPI dashboard uses the same `CandidateFeatures` objects to expose flags, multipliers, and honeypot reasons; it does not infer those values from reasoning text.

## 7. Battle-proof release envelope

V6 keeps expensive ranking work in container-local temporary storage, verifies
the exact champion CSV, then performs a small atomic publish on the destination
filesystem. A deliberate 3-GiB OOM exited 137 while preserving the prior output
and leaving zero mounted temporary files. The release also rejects altered input
bytes, model drift, nondeterministic thread settings, malformed records and
invalid programmatic configuration.
