# Judge proof package — verify everything in ~2 minutes

This page consolidates the evidence that already exists in the repository so it is impossible to miss.
Every claim here is reproducible from the repo; nothing below is a hidden-score or leaderboard claim.
All ranking-quality numbers are **development proxies** (independent heuristic + LLM-judge labels) —
**no official hidden labels were available before submission.**

The submission's defensible edge is **full-pool reproducibility, determinism, integrity gates, and
exact explainability** — not a claim about an unavailable leaderboard score.

---

## 1. One-command reproduction

```bash
PYTHONHASHSEED=0 python rank.py --release \
  --candidates candidates.jsonl --out submission.csv --workers 2
```
The exact same command appears in [`README`](../README.md#reproduce),
[`submission_metadata.yaml`](../submission_metadata.yaml), and [`reproduce.sh`](../reproduce.sh) —
one canonical path, no mismatch.

## 2. Full-pool regeneration proof

Re-ranking the full 100,000-candidate private pool from scratch reproduces the committed
`submission.csv` **byte-for-byte**. Details + environment: [`REGENERATION_PROOF.md`](REGENERATION_PROOF.md).

```
Release verified: frontier-v5, SHA-256 8f7f30c68ec30cb6…
Loaded 100000 candidates; ranked pool 100000; honeypots detected 53; honeypots in output 0
```
- Regenerated SHA-256 == committed SHA-256: **byte-identical** ✅
- The private pool is `.gitignore`d (not redistributed); place the official `candidates.jsonl` at the
  repo root to reproduce.

## 3. Golden-hash proof

- `submission.csv` SHA-256: `8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`
- Pinned and gated by [`tests/test_submission_gate.py`](../tests/test_submission_gate.py): the committed
  bytes must match this hash, and a fixed 2K-slice re-rank must match a recorded behavior hash (catches
  any silent ranking change in seconds).

```bash
sha256sum submission.csv      # -> 8f7f30c68ec30cb6…
bash reproduce.sh             # runs the gate + hash check
```

## 4. Validator proof

```bash
python scripts/validate_submission.py submission.csv      # -> "Submission is valid."
```
Shape/format/membership checks; also runs as a CI gate on every push.

## 5. Test summary

- **270 passed, 1 environment skip** (`PYTHONHASHSEED=0 python -m pytest -q`).
- Includes the golden-hash gate, the 2K-slice behavior gate, the explainability faithfulness test,
  dashboard smoke/parity, integrity-card mapping, and the anti-drift metrics-manifest gate.
- CI gates the suite + validator on every push (`.github/workflows/ci.yml`).

## 6. Determinism + runtime

- Serial and parallel (`--workers`) output are **byte-identical**; pinned BLAS/hash environment;
  reproduced across host CPU counts inside a pinned Docker image.
- Full 100K at 2 CPU / 16 GiB: **136.0 s pipeline / 149.1 s wall** (budget 300 s). Matrix:
  [`runtime_matrix.md`](runtime_matrix.md).

## 7. Integrity gates

- Honeypot and JD-disqualifier multipliers are **hard guardrails** a higher relevance score cannot
  override. On the shipped run: **53 detected in the pool, 0 in the top-100.**
- The distinction is stated honestly: detector-flagged anomaly ≠ confirmed contradiction ≠ official
  planted honeypot. A downstream layer maps suspicious timelines to `VERIFY` for human review; it never
  asserts fraud and never reorders candidates.

## 8. Explainability + ablation + stability

- **Exact** per-feature attributions: because the relevance is a normalized weighted sum, each
  feature's Shapley value *is* its own additive term — analytic, not sampled, byte-reproducible.
  Module [`src/redrob_ranker/explain.py`](../src/redrob_ranker/explain.py); method + commands in
  [`EXPLAINABILITY.md`](EXPLAINABILITY.md). Faithfulness verified by
  `tests/test_explain.py::test_reconstructs_universal_v2` (reconstructs the universal-v2 evidence base).
  Scope: this decomposes the evidence base; the final `frontier-v5` order adds an RRF hedge, a top-band
  correction, integrity backfills, and two tie-breaks on top of it (not folded into the attribution).
- **Ablation:** the pre-registered measured-negatives ladder — every rejected idea (dense embeddings,
  LearnedLR, LambdaMART v2/v3, cross-encoder, rank fusion) is reproducible:
  [`measured_negatives.md`](measured_negatives.md).
- **Stability:** deterministic, label-free leave-one-feature-out rank bands (in `explain.py`).
- **Semantic/embedding path:** built but **disabled by default** (`--use-embeddings` opt-in) — our
  measurements show no benefit (NDCG@10 +0.0000 at ~2.2× runtime), so the semantic-edge claim is
  **removed, not made**.

## 9. Competitor positioning (honest, aggregate)

Across the discoverable public field (Redrob / Redrop / India Runs / Hack2Skill candidate-ranking
repos), on **development proxies** this submission sits in the **top cluster**. It is likely strongest
on **full-pool reproducibility, determinism, integrity gates, and test/explainability proof** — several
strong rivals ship learned/semantic stacks but do not commit a reproducible full-pool submission, and
the whole field shares the same ceiling (self-generated, single-role proxy labels, no official ground
truth). This is **not** a confirmed hidden-score result or leaderboard position.

## 10. Why this is defensible

| Edge | Evidence (this repo) |
|---|---|
| Full-pool reproducibility | §1–§2: one command regenerates the committed artifact byte-for-byte |
| Determinism | §6: serial/parallel byte-identical, pinned env, cross-CPU-count Docker |
| Integrity | §7: hard honeypot/disqualifier gates, 53 detected / 0 shipped |
| Exact explainability | §8: analytic Shapley attributions, faithfulness-tested |
| Honest evaluation | §5, §8: 270 passing tests, pre-registered measured-negatives, dev-proxy labeling |
| No overclaiming | dev-proxy labels stated everywhere; no hidden-score or leaderboard claim |

> Boundary: official hidden labels and numeric judging weights are unpublished. The defensible claim is
> *strongest balanced, fully reproducible, and explainable artifact* — not guaranteed first place on any
> official or isolated metric. Historical R&D notes (superseded framing/codenames) live under
> [`archive/`](archive/) with a disclaimer.
