# Methods & Labels Extraction — Competitor Field

Concrete technical detail. Items marked **[inspected]** were read from source; **[claim]** are from
the pasted report and are unverified (the repo ships no runnable proof or wasn't read).

## Our label arbiter (for reference)
- `artifacts/h2_availblind_labels.jsonl` — 100K rows, schema
  `{candidate_id, tier (0–5 int), relevance (float), reasons[]}`. Frozen before tuning;
  full-population. Reason tags include `production_evidence`, `built_retrieval_ranking`,
  `target_title`, `yoe_in_band`, `reachable`, `preferred_location`, `services_no_product`.
- Secondary proxies (lab worktree): `second_layer_pack_100k/proxy_labels.jsonl` (deterministic
  rubric, 1000), `merged_j1/2/3.jsonl` (3-way LLM judge, 530), `relabel_j1..4.jsonl` (sparse, 32–135).
- LLM-judge sets used `tier>=3` = "relevant" for P@10/MAP (see `src/redrob_ranker/eval_harness.py`).

## Genuine peers above us (inspected this session)

### Thermo041/Indiaruns — 0.886 blind  [inspected]
- **Ranker:** `ranking/rank.py` (1,051 LOC), **Python stdlib only** + multiprocessing. Term-hit
  category scoring: `CORE_WEIGHTS` = retrieval .22 / ranking .20 / vector_search .18 / evaluation
  .16 / llm_ml .13 / python_systems .11; `category_score = clamp(0.20·text_hits + 0.22·skill_hits)`.
- **Differentiator:** polished **Next.js/Vercel dashboard** (`components/dashboard/talent-dashboard.tsx`,
  504 LOC) — read-only viewer over precomputed JSON. Runtime 20.4s.
- **Why it scores high:** heavy availability weighting aligns with the availability-aware blind set;
  **40% of its unique picks are JD-disqualified** by our model (pure_research ×9, title_hopper ×4,
  salary_inversion ×4). Not a real-label advantage.

### Preethamkumarkothakonda/redrob_ai_smart_recruiter (SmartRecruiter) — 0.865 blind  [inspected deps]
- **Pipeline:** `embeddings/generate_embeddings.py` → `indexing/build_faiss_index.py` →
  `ranking/build_candidate_pool.py` → `ranking/retrieve_candidates.py` → `ranking/rerank_candidates.py`
  → `ranking/career_reranker.py`. A real **6-stage FAISS + cross-encoder** pipeline.
- **Deps:** `numpy pandas scikit-learn sentence-transformers faiss-cpu torch transformers` →
  **compliance risk**: torch (+180 MB), FAISS, model download, non-determinism across CPU counts —
  the offline/no-GPU/≤5min/≤16GB sandbox could fail to reproduce it.
- **Why it scores high:** 34% of unique picks JD-disqualified (pure_research ×8, title_hopper ×7);
  unique-pick behavior 0.426 vs our 0.611. Proxy-inflated.

### anishanandhan/RedrobIQ-AI — 0.864 blind  [inspected deps/tests]
- **Structure:** `rank.py` + `validate_submission.py`; tests `test_honeypot.py`, `test_scoring.py`,
  `test_reasoning.py`, `test_sanitize.py`, `test_headers.py`, `test_cli.py`; `hf_space/app.py`
  with a `security/headers.py`. **Cleanest competitor engineering** (deterministic, tested, CI per
  report claim). Submission file: `team_anish.csv`.
- **Why it scores high:** 38% of unique picks JD-disqualified (pure_research ×6, junior_for_senior
  ×5, cv_speech_robotics ×5); unique-pick behavior 0.457 vs our 0.611. Proxy-inflated.

## Other inspected repos (prior sessions)

### datapiratepy/redrob-ranker — 0.854  [inspected]
- `pyyaml`-only, 7 documented phases (`docs/phase1..7`). **Phase 6 investigated a semantic layer and
  rejected it for a 44-template table** (`docs/phase6_semantic_investigation.md`) — independently
  corroborates our measured-negative #1. Honeypot detection, reasoning engine, tests.

### krish57-bit/redrob-ranker — 0.800  [inspected]
- `src/ranker/semantic.py`: **TF-IDF + TruncatedSVD (LSA, 256-dim, seed=42)** default; optional
  precomputed MiniLM. `scoring.py` weights: evidence .32 / title .18 / skills .16 / **semantic .12**
  / yoe .10 / location .08 / logistics .04. Ships the exact semantic lever we measured flat.

### swaraj3092/redrob-ranker — 0.693  [inspected]
- `ranker/pipeline.py` 5-layer; `DISQUALIFIER_MULTIPLIER=0.04`; consulting>0.92, ghost, zero-tech
  rules. pandas-only, no test suite.

## Report-claimed methods (unverified — repo ships no scoreable submission or not read)
- **dheeraj-droid/REDROB (WorthyHire):** rule → BGE-small → cross-encoder. **Measured 0.832, NDCG@10
  0.857** (real, beats us on top-10). [measured]
- **kanish-techjays (Fitjays):** LightGBM LambdaRank, 73 features / 27 trees, 100K Qwen-7B labels [claim]; measured 0.756.
- **sskuntal29:** XGBoost 600 trees + BGE-Large, "Spearman 0.9924" [claim]; measured 0.753.
- **stack-rishi/Ai-Recruiter:** dense + PageRank + BM25 PRF + cross-encoder, 14s [claim]; measured 0.688.
- **bipinmaurya5567-bit/India_Runs-Ranker:** BM25 → bi → cross-encoder → behavioral + RRF [claim]; measured 0.639.

## Clever techniques worth noting (regardless of overall rank)
1. **Cross-encoder reranking of a small top-K** (WorthyHire, SmartRecruiter) — the only technique that
   produced a **higher NDCG@10 than ours** (0.857 vs 0.829). NDCG@10 is 50% of the prize weight.
2. **RRF fusion of multiple channels** (bipinmaurya, stack-rishi) [claim] — ensemble we logged as a
   measured-negative once, but never with cross-encoder channels.
3. **PageRank/graph signal** (stack-rishi) [claim] — untested structural feature class for us.
4. **Polished web dashboard** (Thermo041) — presentation lever; we matched it with the upgraded HF Space.
