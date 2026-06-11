# Deck Outline

## 1. Problem

Keyword filters miss real fit and over-rank candidates who list AI buzzwords without production evidence.

## 2. JD Interpretation

The ideal candidate has production retrieval/ranking/search experience, product-company exposure, Python/evaluation skill, 5-9ish years, India/logistics fit, and strong Redrob availability signals.

## 3. Architecture

Candidate JSONL -> BM25 lexical score -> 28 deterministic features -> behavioral/honeypot/disqualifier multipliers -> top-100 CSV with grounded reasoning.

Dashboard payloads expose the same feature values, flags, and multipliers used by the ranker, not guesses derived from explanation text.

## 4. Feature Matrix

Skills, career, experience, behavior, and logistics are scored separately so the system can tell keyword lists apart from recruiter-plausible fit.

## 5. Multipliers

Behavior is multiplicative because a perfect paper profile with poor response/activity is not hireable. Honeypot and disqualifier multipliers keep impossible profiles away from top ranks.

## 5b. The JD compiles into a deterministic scoring program

`rank.py --jd file.txt` parses any plaintext JD into a frozen `CompiledJD`
(skill groups, weights, title family, locations, experience band) executed by
the same scoring engine. Compiling the bundled challenge JD reproduces the
hand-tuned configuration byte-for-byte (locked by tests); a bundled
Senior-Backend-Engineer demo JD compiles to a visibly different program —
generality, not a one-JD hack.

## 5c. Why each layer earns its place (ablation ladder)

Measured on the 20K dev slice (independent labels, challenge composite):
naive keyword counting 0.6128 -> BM25 0.7158 (+0.103) -> +28-feature matrix
0.7671 (+0.051) -> +multiplicative guardrails 0.7831 (+0.016, and 0 honeypots
in top-100). Dense embeddings: tested, rejected (+0.0000 NDCG@10, ~2.2x
runtime). Every layer pays measured rent; the one that didn't was cut.

## 5d. Hand-tuned weights beat a trained model (appendix)

Cross-validated logistic regression on the exact same 28-feature+BM25 inputs,
trained on the independent labels, loses to the hand weights even on those
labels (composite 0.8238 vs 0.8811; top-100 overlap and coefficients in
docs/learned_weights_appendix.md). Explainable hand weights ship.

## 6. Reproducibility

One command, CPU-only, no network:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

Measured full run (python:3.11 Docker, the Stage-3 environment), current code: 100,000 candidates in 124.7 s worst-case serial on 2 CPUs (80-82 s on a clean 2-vCPU cloud runner; ~58-73% headroom under the 300 s limit), peak container memory ~6.1 GB vs the 16 GB budget; every run byte-identical to the committed submission. 53 honeypots detected, 0 in the top 100. Full matrix: docs/runtime_matrix.md.

## 7. Example Output

Show top candidates with exact title, YOE, relevant skills, production evidence, location, response rate, and notice period.
