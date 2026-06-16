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

## Conclusion

MC4 is a genuine, defensible, rarely-used method that produces the **highest validated composite
on disk (0.8755)** — but it is the **same (B) bet** as fusion-raw, with marginally more exposure to
the anachronism class. It only wins if the hidden labels do **not** penalise impossible tenure
(i.e., no human manually date-checks technology age). Under that world it is the strongest single
artifact available; under the opposite world it is the worst.

There is no clean algorithmic #1 here. The only remaining lever is the **A/B ship decision** (how
much anachronism exposure to accept), not a new model. Logged as a measured finding; golden remains
the risk-averse floor, fusion-raw and MC4 are the validated higher-upside (B) artifacts.
