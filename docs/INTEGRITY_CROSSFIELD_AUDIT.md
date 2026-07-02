# Integrity cross-field audit (2026-07-02)

## Decision

Ship the candidate-ID-agnostic three-way consistency gate on top of the existing
`frontier-v5` relevance ranker. It closes a concrete integrity gap without changing
the relevance scorer or tuning to candidate IDs.

## Rule

A profile receives the review signal `summary_career_yoe_contradiction` only when:

1. the summary explicitly states years of experience;
2. the summed career durations corroborate that statement within 1.5 years; and
3. structured `years_of_experience` exceeds the stated value by at least 3 years.

The signal receives the existing 0.05 softened integrity multiplier. This is an
effective shortlist exclusion and a review flag, not a claim of proven fraud.

## Full-pool evidence

- 100,000 candidates scanned.
- 11 high-confidence three-way contradictions found.
- 9 were already caught by another integrity rule.
- 2 newly covered profiles were in the prior top 100:
  `CAND_0039754` (rank 8) and `CAND_0010770` (rank 84).
- The replacement members are `CAND_0053695` (rank 91) and
  `CAND_0042506` (rank 96).
- Current detector total: 55 profiles; detector-flagged profiles in top 100: 0.

The rule also has explicit false-positive regression tests: it does not fire when
the summary matches the structured field but career history is shorter, or when
career history does not corroborate the summary.

## Evaluation, including the uncomfortable result

Seven existing development-label families were checked under both unlabeled-item
policies. Those relevance-only proxies do not encode the new cross-field integrity
failure, so the exclude policy improves 3/7 and loses 4/7; the zero policy improves
4/7 and loses 3/7. This mixed result is retained here rather than hidden.

The challenge specification treats planted impossible profiles as tier 0. When the
11 independently detected contradictions are assigned that specified risk outcome,
the corrected artifact improves all 7/7 label families under both policies. Mean
composite delta is +0.0619 for exclusion and +0.0377 for zero-fill, with every
individual delta positive.

This is not an official hidden-score result. The shipping decision rests on the
explicit challenge integrity objective, full-population evidence, ID-independent
logic, targeted false-positive controls, and deterministic release proof.

## Release proof

| Gate | Result |
|---|---|
| Host `--release` | 110.5 s; exact golden hash |
| Docker `--cpus=2 --memory=16g --workers 2 --release` | 105.3 s pipeline / 117.2 s container wall; exit 0; not OOM-killed |
| Output | 100 rows; all IDs belong to the source pool |
| Determinism | host, repeat, release, and constrained-Docker CSVs byte-identical |
| Golden SHA-256 | `3d2dbd8a68a145c25bda8122cdf02953ae5f06e2b003aa0f7b4d0e52ce283f6b` |

## Limits

- Development labels are proxies, not the official hidden evaluation.
- The gate recognizes explicit English summary phrasing; it is intentionally narrow
  to favor precision over recall.
- A detector flag means “requires review,” not “candidate committed fraud.”
