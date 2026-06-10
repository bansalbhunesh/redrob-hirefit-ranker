# Agent Guide

## Mission

Produce a reproducible top-100 candidate ranking for the Redrob Senior AI Engineer JD.

## Safe Changes

- Improve feature extraction and weights.
- Improve grounded reasoning.
- Add tests and docs.
- Improve BM25 scoring, deterministic feature extraction, or guardrail calibration.

## Dangerous Changes

- Network calls in `rank.py` or `src/redrob_ranker/`.
- GPU-only dependencies.
- Hidden manual steps.
- Reasoning generated independently from candidate facts.
- Candidate-ID hard-coding.

## Validation Checklist

- `pytest` passes.
- Full ranking creates exactly 100 rows.
- Official validator prints `Submission is valid.`
- Scores are non-increasing.
- Top rows are explainable in an interview.
- `submission_metadata.yaml` matches portal metadata before upload.
