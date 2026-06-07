# Deck Outline

## 1. Problem

Keyword filters miss real fit and over-rank candidates who list AI buzzwords without production evidence.

## 2. JD Interpretation

The ideal candidate has production retrieval/ranking/search experience, product-company exposure, Python/evaluation skill, 5-9ish years, India/logistics fit, and strong Redrob availability signals.

## 3. Architecture

Candidate JSONL -> BM25 lexical score -> 28 deterministic features -> behavioral/honeypot/disqualifier multipliers -> top-100 CSV with grounded reasoning.

## 4. Feature Matrix

Skills, career, experience, behavior, and logistics are scored separately so the system can tell keyword lists apart from recruiter-plausible fit.

## 5. Multipliers

Behavior is multiplicative because a perfect paper profile with poor response/activity is not hireable. Honeypot and disqualifier multipliers keep impossible profiles away from top ranks.

## 6. Reproducibility

One command, CPU-only, no network:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

## 7. Example Output

Show top candidates with exact title, YOE, relevant skills, production evidence, location, response rate, and notice period.

