# Demo script (≈90 seconds)

Honest framing to say once: "All quality numbers are development proxies — no official hidden labels
were available. The point of this demo is that the result is reproducible, explainable, and integrity-
gated, not that we won a score nobody can see."

## A. One-command reproduction (the headline)

```bash
PYTHONHASHSEED=0 python rank.py --release \
  --candidates candidates.jsonl --out submission.csv --workers 2
sha256sum submission.csv      # -> 8f7f30c68ec30cb6…
```
Say: "Same command in the README, the metadata, and reproduce.sh. It regenerates the exact committed
file — byte-for-byte — from the full 100K pool. Here's the matching SHA."

## B. Validator + gate (10 seconds)

```bash
python scripts/validate_submission.py submission.csv   # "Submission is valid."
bash reproduce.sh                                       # runs the gate + hash check
```
Say: "The committed hash and a 2K-slice behavior hash are pinned in the test suite, so any silent
ranking change fails CI."

## C. Live sandbox (30 seconds)

Open https://huggingface.co/spaces/bansal1234/Hirefit
Say: "The example is populated on load. The release docket pins the hash, tests, runtime, and integrity
facts; the candidate ledger opens each person into an evidence dossier, and the CSV export comes from
the live CPU-only ranker. Upload your own pool to replace the example. The integrity gate detected 53
profiles in the full pool and shortlisted 0; every flag is a review signal, not a fraud accusation."

## D. Explainability (20 seconds)

```bash
PYTHONHASHSEED=0 python scripts/explain_report.py --candidates candidates.jsonl \
  --out-md docs/explainability_report.md --out-csv artifacts/attributions.csv --top-k 100
```
Say: "Each candidate's evidence score decomposes into exact per-feature contributions — analytic Shapley values,
not sampled — plus a leave-one-feature-out rank-stability band. We test that the explanation
reconstructs the universal-v2 evidence score the order is built on."

## E. Close (10 seconds)

Say: "The edge here is full-pool reproducibility, determinism, integrity gates, and exact
explainability. Everything I showed is in `docs/JUDGE_PROOF.md` and verifiable from the repo."
