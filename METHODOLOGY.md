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
   ranker (`scripts/build_independent_labels.py`) → composite 0.881, ruling out
   self-grading.
2. **LLM-as-judge check** (dev-only, never in the ranking path) — a strong model scored
   a stratified sample against the JD:
   **top-10 tiers `[5,5,4,4,5,5,5,5,5,5]`, P@10 = 1.0, NDCG@10 = 0.894**
   (`docs/LLM_JUDGE_EVAL.md`). It also confirmed our behavioral guardrails are *more*
   recruiter-aware than the judge — we correctly down-weighted high-skill candidates
   with 12% response rate that the judge over-rated.

## 6. Reproduce

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

Deterministic, offline, CPU-only, 177-194s for the full 100K pool in the python:3.11 Docker image. Full reproduction,
tests, and architecture details are in [README.md](README.md) and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
