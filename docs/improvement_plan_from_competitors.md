# Improvement Plan From Competitors

Derived from the **measured** field audit (`repo_comparison_matrix.md`), not from report claims.
Priority: P0 (do now) → P3 (don't).

## Revisiting our old assumptions against external evidence

- **Learned models (measured-negative #2/#3): assumption HOLDS — strengthened.** Every learned-model
  submission in the field scores below us on the blind arbiter: Fitjays/LightGBM 0.756,
  sskuntal29/XGBoost 0.753, RohithKalva/LightGBM 0.422. External teams shipping the exact lever we
  rejected do worse. **Do not add a learned model.**
- **Dense embeddings (measured-negative #1): assumption HOLDS.** krish57 (TF-IDF/LSA) 0.800 and the
  FAISS/torch peers do not beat us once their disqualified picks are removed. datapiratepy
  *independently* rejected embeddings for a template table. Keep rejected.
- **Cross-encoder: assumption PARTIALLY OVERTURNED — this is the one real gap.** WorthyHire's
  cross-encoder produces **NDCG@10 = 0.857 vs our 0.829**. NDCG@10 is 50% of the prize. We previously
  treated rerankers as a flat measured-negative, but that was for *dense/LTR* rerankers on the full
  pool — not a **cross-encoder on the top-K**. This specific variant has not been measured by us and
  the field shows it helps top-10. **Worth a guarded, blind-set-gated experiment** (see P2).
- **RRF fusion: assumption SOFT.** We logged RRF as a negative once, but never with a cross-encoder
  channel. Low priority retest.

## P0 — Narrative defense (do now, zero code risk)
| # | Idea | Source | What / why | We lack it? | Risk | 
|---|---|---|---|---|---|
| 1 | Ship this audit (`docs/repo_comparison_matrix.md`, `branch_ranking_report.md`, etc.) | this analysis | Documents that we measured the full field and beat every model-complexity repo on the arbiter | partially | none |
| 2 | One-page `docs/WHY_WE_WIN.md` | — | "Only team that can prove it explored the full solution space and rejected every alternative on evidence — and out-scores the field's cross-encoders/learned models on the frozen blind set" | yes | none |
| 3 | Cross-encoder note in README | WorthyHire (dheeraj-droid) | "We evaluated cross-encoder reranking; it requires torch (+180MB), breaks determinism, risks the offline/≤5min sandbox. We measured composite parity-or-loss and chose reproducibility." | yes | none |

## P1 — Cheap engineering signals (low risk)
| # | Idea | Source | What | We lack it? | Adapt | Impact | Risk |
|---|---|---|---|---|---|---|---|
| 4 | `reproduce.sh` one-command | datapiratepy, most repos | single entrypoint to reproduce `submission.csv` | yes | wrap `rank.py` | judge convenience | none |
| 5 | Streamlit/Gradio sandbox | ~70% of field | live demo | **DONE** (upgraded HF Space) | — | demo parity | none |
| 6 | Precomputed-artifact note | SmartRecruiter, ~50% of field | document our BM25 backend cache / determinism as the "artifact" | yes | doc-only | maturity signal | none |

## P2 — The one substantive lever (guarded, measure first)
| # | Idea | Source | What / why | Adapt safely | Expected impact | Risk |
|---|---|---|---|---|---|---|
| 7 | **Top-K cross-encoder rerank**, blind-set-gated | WorthyHire `0.857 NDCG@10` | Rerank only the top ~50 with a small **CPU/ONNX-quantized, precomputed-offline** cross-encoder; adopt **only if** it beats hand on the 100K blind set AND stays byte-deterministic across CPU counts AND fits ≤5min/≤16GB offline | New module **outside** `final_score`; never touch the golden path; ship behind a flag; re-gate the golden hash | could close the NDCG@10 gap (0.829→~0.857), +~0.014 composite **if** it transfers | **HIGH** — torch/onnx determinism + offline model load; most likely fails the gate like our other rerankers |
| 8 | RRF with a cross-encoder channel | bipinmaurya, stack-rishi | retest RRF fusion now that a cross-encoder channel exists | offline experiment only | low–med | med |

## P3 — Do not do
| # | Anti-idea | Why |
|---|---|---|
| 9 | Add a learned model (LightGBM/XGBoost) | Every external instance scores below us; confirms measured-negative #2/#3. |
| 10 | Full dense/FAISS retrieval | Compliance risk (torch/GPU/download); measured flat (#1). |
| 11 | Touch the core scorer / golden submission | Risks the golden hash `af8f2b32`; the science is locked. |
| 12 | Chase the proxy leaders' availability weighting | Their lead is 34–40% JD-disqualified picks; copying it would *hurt* JD-faithful labels. |

## The single decision that matters before the deadline
Everything except **#7 (top-K cross-encoder)** is narrative/docs. #7 is the only change that could move
a real metric (NDCG@10, 50% weight) — but it directly conflicts with the determinism/offline thesis
that is our biggest differentiator, and our prior rerankers all failed the blind gate. Recommendation:
**attempt #7 as an offline, gated experiment only; ship it only if it passes the blind gate and stays
deterministic. Otherwise ship the narrative and freeze.**
