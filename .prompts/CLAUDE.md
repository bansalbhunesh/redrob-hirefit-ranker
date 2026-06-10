# Claude Instructions

This repo is for the Redrob India Runs Data & AI Challenge.

## Non-negotiables

- The ranking command must run without network access.
- Do not call hosted LLM APIs during ranking.
- Do not require GPU.
- Do not manually edit `submission.csv`; generate it from code.
- Keep candidate reasoning grounded in fields that exist in the profile.

## Commands

```bash
pip install -e ".[dev,demo]"
pytest
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
python validate_submission.py ./submission.csv
```

## Code Style

- Keep scoring constants explicit and explainable.
- Prefer deterministic tie-breaking by `candidate_id`.
- Add comments only when a scoring decision is non-obvious.
- If adding model assets, document whether they are precomputed and ensure the ranking step remains under 5 minutes.

