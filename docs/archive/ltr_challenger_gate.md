# Pre-registered adoption gate: LTR challenger vs shipped hand-tuned scorer

Committed BEFORE any challenger training run, per the project's standing protocol
(docs/sensitivity_sweep.md precedent). This document is the decision rule; the study
that follows it must not be reinterpreted after results are seen.

## Motivation

The strongest realistic rival entry is a learning-to-rank model fitted to labels
recovered from the synthetic generator's own latent structure (the planted honeypot
tells prove such structure exists). We build that rival ourselves. Either it beats the
shipped ranking under this gate — and we adopt it via the documented golden-hash-roll
protocol — or it loses and is committed as a measured negative result alongside the
embeddings gate and the learned-LR study.

## The challenger

- Features: the exact 28 shipped features + clamped BM25 + any *generator-forensics*
  features recovered in the companion study (each documented with its recovery method).
- Model: LightGBM LambdaMART (`objective=lambdarank`), 5-fold out-of-fold ranking,
  `deterministic=true`, fixed seed, single-thread inference, model file committed.
- Guardrails unchanged: behavioral, honeypot, and disqualifier multipliers apply on
  top of the challenger base score exactly as they do for the shipped scorer.
- Training labels: generator-derived labels v2 (full-coverage, rule-based, committed),
  validated against both LLM-judge samples before any training run.

## Adoption rule (ALL must hold, decided in one evaluation pass)

1. **Mean challenge composite across all three label sources** — independent heuristic
   labels, LLM judge #1 (gemini-2.5-flash, 249), LLM judge #2 (gpt-4.1-mini, same 249)
   — improves over the shipped scorer by **>= 0.005**, with 100% coverage on each
   (policy=exclude makes <100% coverage configs incomparable; see sweep doc).
2. **Generator-labels v2 are excluded from the scoring side** of criterion 1 (the
   challenger trains on them; scoring on them would be circular by construction).
3. **Honeypots in top-100 remain 0**, and every committed format/validator test passes.
4. **Docker 2-cpu serial runtime <= 240s** including model inference, measured.
5. **Byte-determinism**: two consecutive container runs produce identical CSVs.
6. The top-100 diff against the shipped submission is reviewed row-by-row by the
   project owner before any hash roll.

If ANY criterion fails, the shipped hand-tuned scorer stands and the study is
committed as a negative result. There is no partial adoption, no re-tuning after the
evaluation pass, and no second bite: one challenger evaluation against this gate.

## Notes on label-hypothesis risk (recorded before results)

If the hidden labels are the generator's latent tiers, the challenger should win
criterion 1 only if generator-forensics labels approximate those tiers better than the
hand weights do — which is exactly the condition under which adopting it is correct.
If the hidden labels are LLM-graded, criterion 1's two judge components capture that
hypothesis. The gate is therefore robust to the label question rather than a bet on it.
