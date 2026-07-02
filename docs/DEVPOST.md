# Devpost copy — Redrob HireFit Ranker

> Honest framing: all ranking-quality numbers are **development proxies** (independent heuristic +
> LLM-judge labels). No official hidden labels were available before submission. We do not claim a
> hidden-score or leaderboard rank.

## Elevator pitch

A deterministic, CPU-only system that ranks the top 100 of 100,000 candidates for a Senior AI Engineer
role — and proves *why* each candidate is there, reproducibly. One command regenerates the exact
submitted file, byte-for-byte.

## Inspiration

Most candidate rankers are impressive demos that can't be re-run and can't explain themselves. For a
hiring decision that's the wrong trade. We built for what a recruiter and a judge can actually trust:
the same input always produces the same shortlist, every candidate's evidence score decomposes into named evidence, and
integrity red flags are hard gates rather than vibes.

## What it does

- Ranks 100K candidates to a top-100 shortlist for the JD, offline and CPU-only.
- Scores each candidate from a 33-feature evidence model over career history, role depth, seniority,
  trajectory, behavior, and logistics — with BM25 as one signal, not the whole story.
- Applies multiplicative honeypot and JD-disqualifier guardrails that a high relevance score cannot
  override (53 suspicious profiles detected in the pool; 0 reach the shortlist).
- Emits grounded, per-candidate reasoning and an exact per-feature explanation of each candidate's evidence score.
- Opens as a populated recruiter workspace: verified release docket, searchable candidate ledger,
  evidence dossier, integrity review context, and top-100 CSV export.

## How we built it

- A deterministic pipeline (`rank.py --release`): pinned BLAS/hash settings, forced BM25 backend,
  exact input/model/output hashes verified before an OOM-safe atomic write.
- A fail-closed release path: corrupt configs/artifacts, count drift, and hash drift all fail closed; a
  forced 3 GiB OOM preserved the previous output.
- Explainability as exact math: because the relevance is a normalized weighted sum, each feature's
  contribution is its exact Shapley value — analytic, not sampled — and we test that the explanation
  reconstructs the shipped score.
- A pre-registered "measured-negatives" ladder: we built and rejected dense embeddings, learned LR,
  LambdaMART, and a cross-encoder because none generalized on a frozen blind set.

## Challenges we ran into

- The hidden labels don't exist before submission, so we built independent development proxies and were
  careful never to overclaim from them.
- Byte-exact reproducibility across host CPU counts required pinning BLAS thread settings (float
  reduction order changes the bytes otherwise).
- The biggest discipline was *not* shipping things that looked good in-sample but failed holdout.

## Accomplishments we're proud of

- The committed `submission.csv` regenerates from the full private pool **byte-for-byte** (SHA-256
  `3d2dbd8a…`).
- 278 tests pass, including golden-hash, upload-safety, browser-escaping, and fast behavior-regression gates.
- Honest, exact explainability instead of a black box.

## What we learned

On this task, bigger models and semantic rerankers didn't beat a small, auditable evidence model on our
blind arbiter — and reproducibility + integrity are the differentiators that survive scrutiny.

## What's next

Real human-labeled validation (the one lever our measurements say is still open), and per-role-family
generalization.

## Built with

Python, NumPy, bm25s, FastAPI, Gradio (Hugging Face Space), Streamlit (read-only research dashboard), Docker, and Render. Scikit-learn was used in measured research experiments, not the shipped ranking path.

## Links

- Live demo: https://huggingface.co/spaces/bansal1234/Hirefit
- Source: https://github.com/bansalbhunesh/redrob-hirefit-ranker
- Judge-proof package: `docs/JUDGE_PROOF.md` · Reproduction: `README.md` · Explainability: `docs/EXPLAINABILITY.md`
