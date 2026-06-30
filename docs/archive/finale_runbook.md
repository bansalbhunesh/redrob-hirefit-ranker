# Finale Runbook — V6 live demo and judge answers

Measured 2026-06-30. The release number judges should hear is the final constrained
Docker run: **100,000 candidates in 136.0 s pipeline / 149.1 s wall** under
`--cpus=2 --memory=16g --workers 2 --release`. The exact output SHA-256 is
`8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`.
Older timings in research logs are historical experiments, not the shipping claim.

## Two-minute live demo

1. Show `job_description.txt`: “The job description becomes a deterministic scoring program.”
2. Run a 5K slice:

   ```powershell
   python rank.py --candidates candidates.jsonl --out demo_a.csv --max-candidates 5000 --workers 1 --bm25-backend bm25s
   ```

3. Show a second role to demonstrate that the ordering changes without retraining:

   ```powershell
   python rank.py --candidates candidates.jsonl --out demo_b.csv --max-candidates 5000 --workers 1 --bm25-backend bm25s --jd demo_jd_backend.txt
   ```

4. Open one candidate’s audit payload. Point to career evidence, behavior signals,
   guardrails, and grounded reasoning.
5. Close with: “The official V6 release is CPU-only, offline, exact-output verified,
   and fails closed before it can publish a bad shortlist.”

## Serving and scale answers

| Judge question | Measured answer |
|---|---|
| “How fast is the dashboard?” | The precomputed top-100 plus audit data serves from memory in about 3 ms per request. |
| “What does live ranking cost?” | 300 real candidates complete in about 0.37 s through the HTTP API: roughly 1.2 ms per candidate on commodity CPU, without GPU or external calls. |
| “At Redrob scale?” | **100K candidates in 136.0 s pipeline / 149.1 s wall** in the final 2-vCPU, 16 GiB release run, producing the exact committed artifact. |
| “Can a failed run corrupt the result?” | No. Release mode writes to a temporary file, validates it, then publishes atomically. A forced 3 GiB OOM preserved the prior output and left zero mounted temporary files. |

## Five lines to memorize

1. **Public field:** “Among 672 valid public outputs, V6 is #1/673 on the seven-evaluator mean, #1/100 on the strongest-union mean, and #3/322 on four-axis balance. It beats main on all 30 tested composites.”
2. **Deep understanding:** “BM25 is only one signal; 33 career, seniority, role-depth, behavior, and logistics features read the candidate behind the keywords.”
3. **Discipline:** “We built dense, logistic-regression, LambdaMART, and availability alternatives. We kept only changes that cleared predeclared gates.”
4. **Integrity:** “V6 detected all 53 traps and emitted zero. Release mode also rejected 10,000 corrupt submissions and 9,750 invalid configurations.”
5. **Battle-proofing:** “Input and model hashes are pinned, configuration fails closed, output is fully validated, and atomic publish protects the last good result even under OOM.”

## Honest positioning

The mission-derived score is **93.7/100**, using weights published in
`docs/CHALLENGE_POSITIONING.md`. This is **not an official Hack2skill score** because
the official page does not publish numeric judging weights. Our evidence supports a
projected public-field position of **#1**, with an honest uncertainty range of **#1–#3**.
