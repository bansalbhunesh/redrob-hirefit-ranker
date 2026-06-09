# LLM-Judge Evaluation (dev-only)

This is a **development-time sanity check**, not part of the ranking pipeline. The
official ranker (`rank.py`) is offline, CPU-only, deterministic, and never calls a
hosted LLM. This check uses an LLM **as a judge** on a small sample *after* ranking,
to answer one question: *is the top of our ranking actually strong, or only strong by
our own heuristics?*

## Method

- Tool: `scripts/llm_judge_labels.py` (dev-only; needs an API key, off by default).
- Judge model: `google/gemini-2.5-flash` via an OpenAI-compatible gateway.
- Sample: 249 stratified candidates — the submission's top ranks plus higher-tier
  candidates from the independent heuristic labels plus a random control.
- Each candidate is scored 0–5 against the Senior AI Engineer JD with an explicit
  rubric (read career history, not keyword lists; down-weight unavailable candidates).
- Scored with `scripts/evaluate_independent.py` (challenge composite definition).

## Result

```text
Top-10 tiers : [5, 5, 4, 4, 5, 5, 5, 5, 5, 5]
P@10         : 1.0000
NDCG@10      : 0.8943
NDCG@50      : 0.8734
MAP          : 0.9117
Composite    : 0.8959
```

Every top-10 pick is tier 4–5 by an independent strong model — the ranking is **not**
keyword spam and is **not** propped up by self-referential heuristic labels. The
LLM-judge composite (0.8959) is slightly **higher** than the non-circular heuristic
harness (0.8810).

### Verbatim top-10 judgments

| rank | candidate_id | LLM tier | judge reasoning |
|---|---|---|---|
| 1 | CAND_0018499 | 5 | Exceptional fit: 7.2 yrs experience, shipped IR/ranking at product companies, strong tech, avail. |
| 2 | CAND_0011687 | 5 | Exceptional fit: Shipped production retrieval/ranking systems, relevant experience, strong availability, perfect background. |
| 3 | CAND_0046525 | 4 | Strong fit, but 60-day notice period and prior consulting-like experience at Genpact AI are slight gaps. |
| 4 | CAND_0002025 | 4 | Relevant experience at product co, shipped search/ranking. Minor gap: location. |
| 5 | CAND_0055905 | 5 | Shipped production ranking/retrieval at product companies, strong fit for experience and skills. |
| 6 | CAND_0071974 | 5 | Shipped production ranking/recsys at Netflix/Meta. Meets experience, skills & hybrid criteria. |
| 7 | CAND_0088025 | 5 | Shipped production ranking/retrieval/recsys, strong evaluation, deep tech depth, and product focus. |
| 8 | CAND_0028793 | 5 | Shipped production search/recsys at product companies; strong eval, LLM, retrieval experience. |
| 9 | CAND_0081846 | 5 | Shipped prod ranking/retrieval at scale, strong evaluation, ideal experience, good availability. |
| 10 | CAND_0039754 | 5 | Exceptional fit: production ranking/retrieval at Meta/Apple, strong evaluation focus, exactly the experience needed. |

The full 249 raw judgments are committed as `docs/llm_judge_eval_labels.jsonl`
(`candidate_id`, `tier`, `relevance`, `why`; synthetic challenge data).

## Notable finding: the behavioral guardrail beats the judge

The judge flagged a few candidates it rated tier-5 that the ranker placed lower or
excluded. On inspection these were mostly **correctly down-weighted** by the ranker's
behavioral multiplier, per the JD's explicit instruction to down-weight
"perfect-on-paper but not actually available" candidates. Example: an 8-year Amazon
Senior MLE the judge called *"good availability"* — but with **recruiter response rate
0.12 and not open to work** (`behavioral_multiplier = 0.42`). The deterministic system
read the hireability signals the surface-level judge missed.

## Decision

**No ranking-logic changes were made.** The pre-agreed rule was: only change ranking
logic if the LLM judge reveals a clear top-10 problem. It did not — the top-10 is
clean. Dense embeddings remain rejected (separate gate already failed: NDCG@10
+0.0000, ~2.2x runtime). The ranking is frozen.

## Reproducing

```bash
export OPENAI_API_KEY=...                    # your key
export OPENAI_BASE_URL=https://.../v1        # OpenAI-compatible gateway (optional)
python scripts/llm_judge_labels.py \
  --candidates candidates.jsonl --jd job_description.txt \
  --out artifacts/llm_labels.jsonl --submission submission.csv \
  --stratify-labels artifacts/independent_labels_100k.jsonl \
  --sample-size 250 --provider openai --model google/gemini-2.5-flash
python scripts/evaluate_independent.py --submission submission.csv \
  --labels artifacts/llm_labels.jsonl --label-source llm-judge
```

Fresh runs write raw labels under `artifacts/` (gitignored). The exact labels behind
this report are committed as `docs/llm_judge_eval_labels.jsonl` for verification.
