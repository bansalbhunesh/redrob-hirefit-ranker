# HireFit V6 — two-minute demo script

## 0:00 — The problem

Show a keyword-stuffed wrong-role profile beside a genuine search/ranking
engineer.

> Keyword filters reward vocabulary. Recruiters need evidence: what someone
> built, at what scale, at what seniority, and whether they are reachable now.

## 0:15 — The live product

Open the HuggingFace Space or product app. Upload a pool, open the ranked list,
then inspect one candidate's feature breakdown and grounded reason.

> HireFit reads the full profile, career history and Redrob activity signals.
> Every score decomposes into 33 named features and three visible guardrails.

## 0:38 — The exact challenge result

Show `submission.csv` and the top-six evidence panel.

> The complete 100K challenge pool finishes in 136 seconds on two CPUs. The
> released top 100 is deterministic and byte-identical across the verified
> environment.

## 0:55 — Integrity without automatic rejection

Show the CONTINUE / CLARIFY / VERIFY / BLOCK decision-support surface.

> V6 detected 53 hard traps and emitted zero. Softer contradictions are marked
> VERIFY for a recruiter—not labeled fraud and not silently auto-rejected.

## 1:13 — Public-field proof

Show the comparison table.

> We compared 672 valid public outputs. V6 is #1 out of 673 on the broad
> seven-judge mean, #1 among the 100 strongest revalidated systems across 15
> judge families, and #3 on equal four-axis balance. No public output dominates
> it across all four axes.

## 1:34 — Battle-proof release

Show the release command and attack matrix.

> The system verifies the exact input, model, backend, environment, counts,
> integrity totals and final output hash before publishing. Ten thousand corrupt
> outputs and 9,750 invalid configurations were rejected. Even a forced OOM
> preserved the previous submission and left no mounted temp file.

## 1:55 — Close

> Most teams ship a ranking. We ship a ranking a recruiter can understand and
> an evaluator can reproduce. We don't rank keyword lists. We rank hireability.

## 30-second version

> HireFit V6 ranks careers, context and intent—not keyword lists. It is #1 on
> our broad public multi-judge benchmarks, processes all 100K candidates in 136
> seconds on two CPUs, explains every rank, and emits zero detected honeypots.
> Its release fails closed if the input, model, environment or output changes.
> The official hidden score is unknown; the measured evidence says this is the
> strongest all-around system we can defend.

## On-screen facts

- `PYTHONHASHSEED=0 python rank.py --release --candidates candidates.jsonl --out submission.csv --workers 2`
- SHA-256 `8f7f30c68ec30cb6…`
- 262 passed / 6 environment skips
- 136.0 s pipeline / 149.1 s wall; 2 CPU / 16 GiB
- 53 detected / 0 emitted
- #1 / 673 mean7; #1 / 100 mean15; #3 / 322 balanced4
