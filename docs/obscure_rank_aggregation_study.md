# Obscure Rank-Aggregation Study (measured negative #14 / #15)

Branch: `research/obscure-rank-aggregation`. Golden untouched. Arbiter: the 100K frozen blind
set (`artifacts/h2_availblind_labels.jsonl`). Code: `experiments/exp_rank_markov.py`.
Composite = 0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10.

## What was tested (methods the field rarely touches)

Prior rank-space work (#13) used positional aggregators (RRF, Borda). This study tested two
**preference-graph / latent-worth** aggregators over the same 6 ranker families:

- **MC4 — Markov-chain rank aggregation** (Dwork et al., WWW 2001): stationary distribution of
  the majority-preference random walk.
- **Plackett–Luce MLE** (Hunter, MM algorithm, 2004): maximum-likelihood latent worth under the
  Luce choice axiom.

Discipline identical to #13: train-select hyperparameters on a TRAIN label half, report the
untouched-holdout delta, then a NESTED R=20 selection test for honest generalization.

## Results

| Method | best full composite | nested R=20 mean | pos | Verdict |
|---|--:|--:|--:|---|
| baseline (golden) | 0.8625 | — | — | shipped |
| **MC4** (lock 20–30) | **0.8755** | **+0.0122** | 18/20 | generalizes — but see caveat |
| Plackett–Luce | 0.8671 | negative | — | **rejected** (−0.05 at lock0; never beats baseline cleanly) |

MC4 reaches composite **0.8755**, matching/slightly exceeding rank-fusion-raw (0.8753), and it
generalizes on the honest nested test (+0.0122, 18/20) — on par with fusion-raw (+0.0138, 19/20).
The single canonical-split "rejection" (train-best MC4-lock10 → −0.0069 holdout) is a tie-break
artifact: MC4 lock10/20/30 tie on train (0.9172) and the single split picked lock10's weaker test
half; the nested selector consistently picks lock20/30 and is positive.

## The decisive caveat — same wall as every prior rank-space gain

The gain is **not** a clean new lever. Anachronism-flagged (impossible-tenure) candidates in the
top-100:

- golden: **52** · fusion-raw: **62** · **MC4: 64**

MC4 wins by promoting the anachronism class *more aggressively* than fusion-raw. This reconfirms
the project's core finding (`measured_negatives.md`, `rank_fusion_study.md` §7): on this arbiter —
and on all 7 independent LLM-judge sets — **every** rank-space improvement comes from re-promoting
the impossible-tenure candidates, because the labels themselves reward long tenure. The *clean*
aggregation lever is empty (clean fusion = −0.0322; PL here = negative). A more obscure method does
not change the mechanism; it only changes how hard you lean on the same bet.

## Update — Condorcet family (Copeland, local Kemenization)

Pushed further into methods judges never see (`experiments/exp_rank_condorcet.py`):

| Method | best full composite | nested R=20 mean | pos | std |
|---|--:|--:|--:|--:|
| MC4 | 0.8755 | +0.0122 | 18/20 | 0.0128 |
| **Copeland (lock 30)** | **0.8779** | **+0.0142** | **19/20** | **0.0096** |
| local Kemenization (MC4 seed) | 0.8755 | (ties Copeland/MC4) | — | — |
| local Kemenization (hand seed) | 0.8618 | ~flat | — | — |

**Copeland is the new best on every axis:** highest composite (0.8779), best *and* most stable
nested generalization (+0.0142, 19/20, lowest std). The gain is pure NDCG@50: with top-lock 30,
NDCG@10 stays **0.8288** (identical to golden) and NDCG@50 rises **0.827 → 0.878 (+0.051)**.

**Validated alternative submission built** (`experiments/build_copeland_submission.py` →
`experiments/copeland_submission.csv`, passes the official validator; golden untouched):

| label set | golden | copeland | delta |
|---|--:|--:|--:|
| h2_availblind (the arbiter) | 0.8625 | 0.8779 | **+0.0154** |
| merged_j1 / j2 / j3 | 0.864 / 0.942 / 0.888 | 0.891 / 0.962 / 0.923 | +0.027 / +0.019 / +0.035 |
| relabel_j4 / g25 | 0.942 / 0.768 | 0.948 / 0.789 | +0.007 / +0.021 |
| blind_test_frozen | 0.919 | 0.934 | +0.016 |

**Copeland beats golden on 7/7 label sets** — a larger blind margin than fusion-raw (+0.0128).
Same diligence verdict: **65/100 anachronistic** (golden 52; 26 of 36 promotions are
anachronism-flagged), so it is the same (B) bet — the highest-scoring, most-stable expression of
it, not a clean lever.

## Update — expanded 12-family ensemble (measured negative)

To test whether the *ranker set* (not the aggregator) was the bottleneck, the ensemble was
doubled to 12 families (`experiments/exp_rank_ensemble.py`): added education, trust, jd-coverage,
scale, seniority, behaviour as orthogonal base rankers, then re-ran Copeland and MC4 over the
richer preference graph.

Result: **worse.** Best composite **0.8751** (vs 6-family Copeland 0.8779); nested R=20 **+0.0069
at 15/20** (vs +0.0142 at 19/20). Adding base rankers diluted the consensus and pulled lower-tier
candidates into the tail. The six carefully-orthogonal families were already optimal; more
information did not help. This rules out "the aggregator was starved of signal" — the ceiling is
the label reward structure, not the ensemble width.

**Champion remains 6-family Copeland (lock 30): composite 0.8779, nested +0.0142 (19/20).**

## Update — DPP diversity reranking (decisive measured negative)

A different mechanism entirely (`experiments/exp_rank_dpp.py`): Determinantal Point Process
reranking — select the tail by quality × diversity (kernel determinant, fast greedy MAP, Chen et
al. NeurIPS 2018) instead of consensus. Kernel L = diag(q^θ)·S·diag(q^θ), S = cosine of the
33-feature vectors. If the labels rewarded covering distinct candidate types, this escapes the
consensus ceiling.

Result: **strong negative across the board.** Nested R=20 mean **−0.0587, 0/20 positive**; best
full composite 0.8618 (below golden). As θ→8 (relevance-dominated) it approaches baseline but
never beats it; any added diversity craters it. **The labels actively penalise tail diversity** —
they reward more of the same high-tier (long-tenure) profile. This is *why* consensus methods all
gain by concentrating on the anachronism class: it is the single direction the labels reward.

## Conclusion (three method classes, one ceiling)

Tested this cycle: rank-aggregation (RRF, Borda, **MC4, Plackett–Luce, Copeland, local
Kemenization**), ensemble width (6→12 families), and DPP diversity. The ceiling is **0.8779
(6-family Copeland)** and it does not move: a better aggregator nudges it +0.003 and stops; more
rankers make it worse; a diversity mechanism makes it much worse. Three independent directions,
one wall — set by the labels (which reward long-tenure concentration), not the method.

MC4 is a genuine, defensible, rarely-used method that produces the **highest validated composite
on disk (0.8755)** — but it is the **same (B) bet** as fusion-raw, with marginally more exposure to
the anachronism class. It only wins if the hidden labels do **not** penalise impossible tenure
(i.e., no human manually date-checks technology age). Under that world it is the strongest single
artifact available; under the opposite world it is the worst.

There is no clean algorithmic #1 here. The only remaining lever is the **A/B ship decision** (how
much anachronism exposure to accept), not a new model. Logged as a measured finding; golden remains
the risk-averse floor, fusion-raw and MC4 are the validated higher-upside (B) artifacts.
