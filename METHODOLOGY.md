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
   → 28-feature recruiter matrix    (skills, career evidence, seniority, behavior, logistics)
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
| **Feature matrix + BM25, not an LLM scoring each candidate** | An LLM-per-candidate can't scale to 100K under a real latency/cost budget (the JD makes this point itself), isn't reproducible, and needs network. We rank the whole pool on CPU in about 3 minutes worst-case in the eval Docker image. |
| **No dense embeddings — *tested and rejected*** | We built a model2vec/potion dense-retrieval branch and gated it on a measured A/B: **NDCG@10 +0.0000, ~2.2× runtime → FAIL**. We shipped the simpler, faster system; the negative result is documented (`artifacts/embedding_gate_result.txt`). |
| **Career-evidence over keywords** | Production/IR-ranking signals mined from career *history* (weights 0.13 + 0.12) outweigh skill-list matches — this is how Tier-5 candidates without the buzzwords still surface. |
| **Multiplicative behavioral & honeypot guardrails** | A high fit score cannot rescue an impossible profile or an unavailable candidate. This encodes the JD's explicit "down-weight the unavailable" instruction. |
| **Deterministic everything** | Same input → byte-identical output (hash seed pinned). Every score is traceable and debuggable — essential for explainability and reproduction. |

## 4. Explainability

- **Per-candidate reasoning** in the output CSV is generated **only from facts in the
  profile** (title, years, named skills, signal values) — no hallucinated skills.
- **Every score decomposes** into named features and the three multipliers; nothing is
  a black box.
- The **interactive dashboard** ([Render](https://redrob-hirefit-ranker.onrender.com))
  shows the pipeline stages, honeypot blocking, and a per-candidate feature + reasoning
  audit live.

## 5. How we validated ranking quality (without the hidden labels)

1. **Non-circular heuristic eval** — an independent labeler sharing *no code* with the
   ranker (`scripts/build_independent_labels.py`) → composite 0.886 (post-calibration;
   0.881 pre-calibration baseline), ruling out self-grading.
2. **LLM-as-judge check** (dev-only, never in the ranking path) — a strong model scored
   a stratified sample against the JD:
   **top-10 tiers `[5,5,4,4,5,5,5,5,5,5]`, P@10 = 1.0, NDCG@10 = 0.894**
   (`docs/LLM_JUDGE_EVAL.md`). It also confirmed our behavioral guardrails are *more*
   recruiter-aware than the judge — we correctly down-weighted high-skill candidates
   with 12% response rate that the judge over-rated.

## 5b. Four measured negative results

Recited consistently across README, deck, and this document — every alternative was
built, measured against a rule fixed in advance, and committed when it lost:

1. **Static dense embeddings** (model2vec/potion-32M): NDCG@10 +0.0000 at ~2.2×
   runtime → rejected by the pre-committed gate.
2. **Learned logistic-regression weights**: composite 0.8238 vs 0.8811 hand-tuned,
   even on labels that structurally favor the learner (docs/learned_weights_appendix.md).
3. **LambdaMART challenger** on the shipped 28 features + recovered generator
   structure, trained on ~1.5K LLM judgments: −0.0061 against a pre-registered
   +0.005 adoption gate (docs/ltr_challenger_study.md).
4. **Declined availability hedge**: +0.0135 only under an availability-blind label
   hypothesis that the JD's own down-weight instruction contradicts; declined and
   documented before any artifact change (docs/hedge_simulation_study.md).

## 6. The consensus calibration pass — the single unfreeze

After the ranking was frozen, an exhaustive pairwise audit of the top-100
(`scripts/top100_ordering_audit.py`) found 61 swaps that improve the challenge
composite under **all three** label sources simultaneously (independent
heuristic, LLM judge 1, LLM judge 2 — each at 100% coverage). Because that
screen tested 4,950 pairs against correlated proxies, nothing was adopted
until the gain survived **held-out validation**
(`scripts/swap_holdout_validation.py`): swaps selected on two sources only,
evaluated on the judge that played no part in selection, both crossover arms.
Result: aggregate +0.0106 / +0.0086 with **zero negative per-swap held-out
deltas**, robust to the DCG gain convention, every composite independently
recomputed outside the harness. Scope honesty, stated verbatim from the study:
judge 1 and judge 2 scored the *same 249 ids* (kappa 0.935), so this holds out
the **rater, not the sample**.

On that evidence — which clears the same pre-registered +0.005 adoption bar
the LTR challenger failed — the conservative greedy-eight three-source
consensus swaps were adopted as a deterministic calibration pass
(`src/redrob_ranker/calibration.py`): eight pairwise preferences, applied only
on the bundled challenge JD, exchanged only when misordered, no change to
top-100 membership (honeypots remain 0), score ladder unchanged. The two
largest demotions are 3.0- and 4.2-year profiles outside the JD's 5–9 year
band that all three sources agreed were over-ranked — the calibration
corrects real YoE-band misorderings, not label noise. The submission is
**permanently frozen** after this roll; the evidence chain is
docs/top100_ordering_audit.md → docs/swap_holdout_validation.md → the module.

## 7. Reproduce

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

Deterministic, offline, CPU-only: 80 s on a clean 2-vCPU cloud runner (CI-verified),
187 s conservative worst-case serial in local Docker (full matrix:
docs/runtime_matrix.md). Full reproduction,
tests, and architecture details are in [README.md](README.md) and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
