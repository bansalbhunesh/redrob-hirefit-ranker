# Methodology — Redrob HireFit Ranker

How the system ranks 100,000 candidates for the Senior AI Engineer role, and **why**
each technical choice was made. Maps directly to the judging criteria: *ranking
quality*, *methodology clarity*, and *explainability*.

---

## 1. Problem framing — the gap between what the JD says and what it means

The dataset is built to punish keyword filters. The JD asks for "5–9 years,
embeddings/retrieval/ranking," but the *intent* is to find engineers who actually
**shipped** ranking / search / recsys at product companies — even if their profile
never says "RAG" or "Pinecone" — while **rejecting**:

- **keyword stuffers** — wrong-role profiles padded with AI skills,
- **honeypots** — subtly impossible profiles (e.g. "expert" in 10 skills with 0 months used),
- **unavailable** candidates — perfect on paper but not actually hireable (no response, not open to work).

So the ranker is designed to read **careers and behavior**, not skill lists.

## 2. Architecture (deterministic, offline, CPU-only)

```
candidates.jsonl
   → Parse + structured text
   → BM25 lexical relevance        (one signal)
   → 33-feature recruiter matrix    (skills, career evidence, seniority, role-family depth, behavior, logistics)
   → Weighted base score
   → × Behavioral multiplier        (availability / responsiveness)
   → × Honeypot multiplier          (hard 0 for impossible profiles)
   → × Disqualifier multiplier      (consulting-only, CV/speech-only, keyword-stuffer, wrapper, junior)
   → Deterministic top-100 + grounded reasoning → submission.csv
```

The final score is `base_score × behavioral × honeypot × disqualifier`. Guardrails are
**multiplicative**, so a perfect-looking but unhireable / impossible / off-target
profile is pushed down regardless of how strong its keywords look.

## 3. Key technical choices — and the reasoning

| Choice | Why |
|---|---|
| **Feature matrix + BM25, not an LLM scoring each candidate** | An LLM-per-candidate cannot scale to 100K under the challenge latency/cost budget, is not reproducible, and needs network. The release ranks the full pool in **105.3 s pipeline / 117.2 s wall** in the final 2-vCPU, 16 GiB Docker release run. |
| **No dense embeddings — *tested and rejected*** | We built a model2vec/potion dense-retrieval branch and gated it on a measured A/B: **NDCG@10 +0.0000, ~2.2× runtime → FAIL**. We shipped the simpler, faster system; the negative result is documented (`artifacts/embedding_gate_result.txt`). |
| **Career-evidence over keywords** | Production/IR-ranking signals mined from career *history* (weights 0.13 + 0.12) outweigh skill-list matches — this is how Tier-5 candidates without the buzzwords still surface. |
| **Multiplicative behavioral & honeypot guardrails** | A high fit score cannot rescue an impossible profile or an unavailable candidate. This encodes the JD's explicit "down-weight the unavailable" instruction. |
| **Deterministic everything** | Same input → byte-identical output (hash seed pinned). Every score is traceable and debuggable — essential for explainability and reproduction. |

## 4. Explainability

- **Per-candidate reasoning** in the output CSV is generated **only from facts in the
  profile** (title, years, named skills, signal values) — no hallucinated skills.
- **Every score decomposes** into named features and the three multipliers; nothing is
  a black box.
- The **interactive sandbox** ([Hugging Face](https://huggingface.co/spaces/bansal1234/Hirefit))
  shows the pipeline stages, integrity screening, and a per-candidate feature + reasoning
  audit live. The FastAPI mirror is reproducible from the root `render.yaml` Blueprint.

## 5. How we validated ranking quality (without the hidden labels)

1. **Non-circular heuristic eval** — an independent labeler sharing *no code* with the
   ranker (`scripts/build_independent_labels.py`) → composite ~0.881 (dev proxy),
   ruling out self-grading.
2. **LLM-as-judge check** (dev-only, never in the ranking path) — a strong model scored
   a stratified sample against the JD:
   **top-10 tiers `[5,5,4,4,5,5,5,5,5,5]`, P@10 = 1.0, NDCG@10 = 0.894**
   (`docs/LLM_JUDGE_EVAL.md`). It also confirmed our behavioral guardrails are *more*
   recruiter-aware than the judge — we correctly down-weighted high-skill candidates
   with 12% response rate that the judge over-rated.
3. **Public-field stress test** — 1,367 repositories discovered, 1,279 eligible,
   and 672 valid public outputs. On development proxies the release sits in the top cluster on the seven-evaluator mean,
   the strongest-union mean, and equal four-axis
   balance; it beats main on all 30 tested composites. These are transparent
   local comparisons, not an official leaderboard.

## 5b. Four measured negative results

Recited consistently across README, deck, and this document — every alternative was
built, measured against a rule fixed in advance, and committed when it lost:

1. **Static dense embeddings** (model2vec/potion-32M): NDCG@10 +0.0000 at ~2.2×
   runtime → rejected by the pre-committed gate.
2. **Learned logistic-regression weights**: composite 0.8238 vs 0.8811 hand-tuned,
   even on labels that structurally favor the learner (docs/learned_weights_appendix.md).
3. **LambdaMART challenger** on the shipped 33 features + recovered generator
   structure, trained on ~1.5K LLM judgments: −0.0061 against a pre-registered
   +0.005 adoption gate (docs/ltr_challenger_study.md).
4. **Declined availability hedge**: +0.0135 only under an availability-blind label
   hypothesis that the JD's own down-weight instruction contradicts; declined and
   documented before any artifact change (docs/hedge_simulation_study.md).

## 6. The ordering audit — and why the official path uses no candidate-ID tuning

After the ranking was frozen, an exhaustive pairwise audit of the top-100
(`scripts/top100_ordering_audit.py`) found swaps that improve the challenge
composite under **all three** label sources simultaneously (independent
heuristic, LLM judge 1, LLM judge 2 — each at 100% coverage), validated on a
held-out judge (`scripts/swap_holdout_validation.py`) and re-tested by a third
judge family (deepseek, `docs/llm_judge_eval_3.md`) collected outside the
selection loop. The audit identified real YoE-band and career-evidence
misorderings — not label noise.

Those consensus swaps were briefly trialed as a deterministic calibration pass.
**That pass has since been removed.** Hard-coding candidate-ID preferences in the
official ranking path is the project's single biggest credibility risk, and a
ranker should not need candidate *identity* to order results. The ordering signal
the audit surfaced was instead **generalized into role-family depth scoring**
(backend/data/devops/search), which improves ordering from features alone, with
no candidate IDs.

The official ranking path therefore applies **no candidate-ID swaps**, enforced
in CI: `tests/test_no_calibration.py` asserts `calibration.py` is gone, and
`tests/test_no_cand_id_in_ranking_path.py` fails the build if any `CAND_` id
appears anywhere under `src/`. The full audit evidence chain
(docs/top100_ordering_audit.md → docs/swap_holdout_validation.md →
docs/llm_judge_eval_3.md) is retained for transparency.

## 7. Reproduce

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

Deterministic, offline, CPU-only: 80 s on a clean 2-vCPU cloud runner (CI-verified),
~130–155 s in local Docker (full matrix: docs/runtime_matrix.md). BLAS thread
counts are pinned (Dockerfile + `rank.py`) so the output is **byte-identical
across CPU counts** — golden `submission.csv` SHA-256
`fdfd3f3590720e1260822b6729b2851dc8daca9f3f859cefc3df184bbbd4c5db`, verified at
`--cpus=2` and `--cpus=4` (docs/archive/reproducibility_notes.md). Full reproduction,
tests, and architecture details are in [README.md](README.md) and
[ARCHITECTURE.md](ARCHITECTURE.md).
