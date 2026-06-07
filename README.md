# Redrob Candidate Ranker

CPU-only candidate ranking system for the India Runs Data & AI Challenge.

The ranker scores 100,000 candidate profiles for Redrob's Senior AI Engineer role using **Plan D v2**: BM25 lexical relevance, a deterministic 28-feature recruiter matrix, multiplicative behavioral/honeypot/disqualifier multipliers, and grounded reasoning.

## Features

- BM25 lexical scoring with `bm25s` preferred and `rank-bm25` fallback.
- Named 28-feature matrix across skills, career, experience, behavior, and logistics.
- Skill alias expansion for embeddings, vector DBs, hybrid search, LLM production, Python ML engineering, and evaluation frameworks.
- Multiplicative behavioral model for recency, response rate, open-to-work, interview reliability, recruiter saves, contact verification, assessments, GitHub activity, and notice period.
- Honeypot guardrails for impossible timelines, expert-zero-duration skills, multiple current jobs, salary inversion, education impossibility, endorsement inflation, and title-description contradictions.
- No hosted LLM/API candidate scoring. No network, GPU, or model download during ranking.
- Deterministic, fact-grounded reasoning for the top 100.

## Tech Stack

- Python 3.11+; locally verified on Python 3.14.3
- Core ranker: `numpy`, `orjson`, `bm25s`, `rank-bm25`
- Optional demo: `pandas`, FastAPI, Uvicorn, Gradio

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,demo]"
```

For the lean challenge runtime only:

```bash
pip install -r requirements.txt
```

For the optional FastAPI/Gradio demo:

```bash
pip install -r requirements-demo.txt
```

The official challenge data is not committed. Place `candidates.jsonl` in the repo root or pass its path explicitly.

## Reproduce Submission

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

Optional backend selection:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --bm25-backend auto
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --bm25-backend bm25s
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --bm25-backend rank_bm25
```

Validate with the official validator:

```bash
python validate_submission.py ./submission.csv
```

Local verification on the 100K candidate file completed in 184.1 seconds with `bm25s` and the official validator returned `Submission is valid.`

## Demo

FastAPI:

```bash
uvicorn apps.api.main:app --reload
```

HuggingFace Space:

```bash
python apps/space/app.py
```

## Repository Structure

- `rank.py` - official one-command CLI entrypoint.
- `src/redrob_ranker/` - parsing, BM25 scoring, 28-feature matrix, multipliers, reasoning, and validation.
- `apps/api/` - FastAPI sample-ranking endpoint.
- `apps/space/` - HuggingFace Gradio demo.
- `tests/` - unit and integration tests.
- `docs/` - deck outline and AI usage notes.
- `requirements.txt` - lean ranking dependencies.
- `requirements-demo.txt` - optional demo dependencies.

## AI Tools Usage

AI tools were used for architecture discussion, code scaffolding, and review. Kimi/Claude reference files informed the final design, but no candidate is scored by a hosted LLM. The ranking command is CPU-only, no-GPU, and no-network.
