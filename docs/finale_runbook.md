# Finale Runbook — live demo script + serving-cost answers (measured 2026-06-11)

All numbers below were measured on the dev laptop (12-core, Windows, Python 3.14);
the evaluation Docker numbers (80-82s cloud / 164.9s local, full 100K) are in
docs/performance_audit.md and docs/runtime_matrix.md.

## The 2-minute live demo: "the JD compiles into the ranker"

> Setup beforehand: terminal in the repo root, font large, `PYTHONHASHSEED=0` set.
> Both commands dry-run rehearsed; total live compute ~21s across two runs.

1. **"This is the challenge JD."** (show `job_description.txt` for 5 seconds)

2. **Run the official ranking on a 5K slice** (~8s live):
   ```
   python rank.py --candidates candidates.jsonl --out demo_a.csv --max-candidates 5000 --workers 1 --bm25-backend bm25s
   ```
   Show the top rows; read one reasoning line aloud — point out it cites verbatim
   career facts, not keywords.

3. **"Now a completely different role — Senior Backend Engineer."** (~13s live):
   ```
   python rank.py --candidates candidates.jsonl --out demo_b.csv --max-candidates 5000 --workers 1 --bm25-backend bm25s --jd demo_jd_backend.txt
   ```
   Show both top-10s side by side: the ordering visibly changes from rank 2 down —
   same engine, different compiled scoring program. No retraining, no API calls.

4. **The closer:** "And on the bundled JD, the compiled program is byte-identical
   to the historical pipeline — locked by `tests/test_jd_compiler.py` against the
   golden hash. The JD is the spec. We rank careers, not keywords."

Fallback if live compute is not allowed: the HuggingFace Space (bansal1234/Hirefit)
does the ≤100-candidate version of the same flow in the browser.

## Serving-cost answers (measured, not estimated)

| Question a judge asks | Measured answer |
|---|---|
| "How fast is the dashboard?" | Showpiece payload (top-100 + full audit data) served from memory in **~3 ms** per request (5-request sample: 2.7-3.8 ms). |
| "What does live ranking cost?" | **300 real candidates end-to-end in ~0.37 s** through the HTTP API — upload, full 28-feature pipeline, guardrails, reasoning, JSON audit payload (two-run sample: 0.36/0.39 s). That is ~1.2 ms per candidate on commodity CPU, no GPU, no external calls. |
| "At Redrob scale?" | 100K candidates in 80-82 s on a 2-vCPU cloud container (CI-measured, byte-deterministic) — linear in pool size, embarrassingly parallel across JDs, zero marginal API cost. Score updates are a re-rank, not a retrain. |
| "Per-candidate audit?" | Every ranked candidate carries its full feature/multiplier/flag breakdown in the payload — the audit is precomputed with the rank, not reconstructed on demand. |

## The five recitations (memorize)

1. **Four measured negatives, in order**: static embeddings (+0.0000 at 2.2x runtime);
   learned-LR (0.824 vs 0.881); LambdaMART challenger (-0.0061 against our +0.005
   pre-registered gate); declined availability hedge (+0.0135 only if the labels
   ignore the JD's own down-weight instruction).
2. **The discipline line**: "We measured the config that scores higher and declined
   it; we built our strongest rival and it lost; we unfroze exactly once — and a
   third judge family that didn't exist at adoption time re-tested the change
   afterwards: +0.0124, six of eight swaps confirmed, one tie, one contested
   (docs/llm_judge_eval_3.md). Then we froze permanently."
3. **The Devanagari answer**: "Latin-only normalization is one module
   (`text.py`/`_norm`); the architecture is script-agnostic — the Unicode swap is a
   committed roadmap item in ARCHITECTURE.md and touches neither retrieval logic,
   features, guardrails, nor the JD compiler."
4. **The "high availability next to a 43% response rate" answer**: "The adjective
   reports the composite behavioral multiplier — response rate, notice period,
   open-to-work, recency, interview reliability together
   (`reasoning.py`, `features.py`) — and the numbers beside it are two of those raw
   inputs, printed so a recruiter can audit the adjective rather than trust it. A
   91% responder on a 120-day notice and a 43% responder who is open-to-work,
   recently active, and reliable can both clear the bar; the row shows you why.
   If Redrob would rather the adjective track response rate alone, that is a
   one-line threshold change — the submitted artifact is frozen, so we show the
   mapping in the dashboard's audit payload instead."
5. **The overshoot answer (16-year profile at rank 10)**: "We demote juniors hard —
   below-band falls off a Gaussian and under-3-years takes a further 0.55 cut
   (`features.py`, `yoe_fit_score`) — but we deliberately do not punish surplus
   experience by years alone: every label source we have, including all three LLM
   judge families, rates that 16-year search veteran tier 5, and the JD asks for
   '5–9 years' as a seniority floor in context, not a ceiling. Overshoot risk is
   carried by the trajectory and title features instead: an overqualified profile
   that drifted away from hands-on ranking work loses on career_trajectory, not on
   a years arithmetic. We measured the alternative reading and the labels
   contradict it."
