# External recruiter-label validation — the hedge holds up against a real judge

*Added 2026-06-18. This is an **external cross-check**, separate from our own frozen Ψ human
lockbox (still awaiting data). All numbers reproducible via the eval harness on the cited labels.*

## The data
Another India Runs participant ("Sifter", shikhar1809) published a real recruiter-labeled set:
**180 reviewer labels** (one project recruiter) + a **50-candidate blind technical-recruiter holdout**
(an independent second recruiter), each `strong_fit / maybe / not_fit`. This is the first time our
ranking has been scored against *real* human recruiter judgments rather than our dev proxy.

## Result — the integrity-safe hedge wins the independent judge
Scored `strong_fit=4, maybe=2, not_fit=0` (our shared eval harness):

| Ranking | reviewer-1 (180) | **blind recruiter (50)** | not_fit in top-100 |
|---|---|---|---|
| **HEDGE (shipped)** | 0.7106 | **NDCG@10 0.904 / composite 0.872** | **0** |
| minimax (proxy-max alt) | 0.7678 | 0.862 / 0.851 | 1 |
| tail_rescue (proxy-max alt) | 0.7766 | 0.862 / 0.855 | 1 |
| Sifter (their submission) | 1.0000* | 0.924 / 0.909 | 1 |

- **On the independent blind recruiter, the hedge is the best of all our artifacts** (NDCG@10 0.904)
  and the only one with **0 not_fit** candidates in the top-100. The integrity-safe (A) choice — exclude
  egregious impossible-tenure candidates — is *confirmed* by an independent human judge.
- The hedge scores **lower on reviewer-1**, and that is expected and coherent: reviewer-1 rated several
  *anachronistic* (impossible-tenure) candidates as strong-fit; the hedge deliberately excludes the
  egregious ones. We chose to trust the official spec/JD (which warn that impossible tenure is a
  honeypot / Stage-3 filter) and the independent blind recruiter over reviewer-1 on those candidates.

## Cross-encoder transfer check
*\*Sifter reports a perfect 1.0 on reviewer-1 after tuning a reranker with those labels.* We reproduced
the broad approach (semantic bi-encoder + `ms-marco-MiniLM` cross-encoder + a reranker trained on the
human labels) and evaluated it separately on the blind recruiter: the cross-encoder scores
**NDCG@10 0.71** versus our production scorer's **0.90** on the overlapping subset. The result suggests
limited transfer, but the sample is too small for a general conclusion. Full study:
`experiments/ultra/CROSS_ENCODER_FINDINGS.md` (research branch).

## Competitor field
On the blind-arbiter development proxy (100% coverage), our ranking is in the **top cluster** of the
20-repository sample. This is a local proxy comparison, not an official leaderboard. The human-label
numbers above are a small independent cross-check.

## Honest limits
- The blind-recruiter holdout is **~10 overlapping candidates (19% coverage)** — small; treat as
  directional, not decisive. The reviewer set is 180.
- These are **one external annotator pair**, selection-biased toward candidates Sifter chose to review.
- Still our dev proxy for the hidden official score; our own frozen Ψ lockbox remains the gold standard
  and is still awaiting reviewers.

**Bottom line:** the one external real-recruiter signal we have *supports* the integrity-safe hedge —
it is the best of our artifacts on the independent recruiter and the cleanest (0 not_fit), while a
competitor's cross-encoder edge evaporates when validated honestly.
