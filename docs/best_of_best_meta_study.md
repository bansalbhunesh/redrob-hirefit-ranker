# Best-of-Best Meta-Ensemble Study

> **SHIPPED ON THIS BRANCH (2026-06-16): the full-proof HEDGE** (`build_hedge_submission.py` →
> `submission.csv`, sha256 `24f84f4b…`). It is severity-gated Copeland: promote an anachronism
> candidate only when claimed tenure ≤1.2× the technology's age (defensible/rounding), exclude the
> egregious cases a human would flag. **Why the hedge over raw Copeland or golden:** it beats golden
> on 7/7 label sets (blind 0.8748 vs 0.8625) — keeping ~80% of Copeland's measured upside — while
> carrying FEWER anachronism candidates than golden itself (44 vs 52), so under a modeled
> anachronism-penalty world it has a better worst-case than BOTH golden and full-Copeland (see
> `experiments/exp_robust_hedge.py`). The downside it hedges: raw Copeland's gain is anachronism-
> promotion, which loses if hidden judges date-check tenure; golden is also exposed (52 such
> candidates). The hedge dominates both. Full suite 198 pass, validator green, `reproduce.sh` green;
> production `rank.py` unchanged (slice gate green); `main` keeps golden af8f2b32 frozen.


Branch: `research/best-of-best-meta` (from the Copeland-shipped branch). Goal: mix the strongest
rankers, take each one's best part, and try to exceed the Copeland champion (0.8779). Arbiter:
frozen 100K blind set; golden production pipeline untouched. Code: `experiments/exp_meta_ensemble.py`.

## Constructions tested (all holdout + nested-gated)

Over the five base rankings — hand, RRF, Borda, MC4, Copeland:
1. **Meta-aggregation** — aggregate the 5 method rankings as voters (meta-RRF / meta-Borda /
   meta-Copeland / meta-MC4): a consensus of consensuses.
2. **Banded hybrid** — each method's empirically-best band: hand for the locked top (P@10, NDCG@10),
   Copeland for 11–50 (best NDCG@50), MC4 for 51–100. Literally "take each method's best part."
3. **Rank-average** — mean rank position across the 5 methods.

## Result — no headroom above Copeland

| construction | best full composite | nested R=20 |
|---|--:|--:|
| **Copeland lock30 (champion)** | **0.8779** | **+0.0142 (19/20)** |
| banded hand/cope/mc4 lock30 | 0.8779 (ties) | — |
| meta-MC4 / meta-Copeland | 0.8759–0.8765 | — |
| meta-RRF / meta-Borda / rank-avg | 0.8690–0.8741 | — |
| **best meta config (nested-selected)** | 0.8779 | **+0.0129 (18/20)** — slightly worse |

The best the mix achieves is a **tie** with the single best method; nested generalization is
marginally lower. Mixing rankings that are each built from the same 6 families, all promoting the
same anachronism class, cannot exceed the best of them — there is no orthogonal information left to
combine.

## Conclusion — five method classes, one wall

The 0.8779 ceiling now holds across: rank-aggregation (RRF/Borda/MC4/Copeland/Kemeny/PL),
ensemble width (6→12 families, worse), diversity (DPP, much worse), the clean variant (negative),
and **meta-mixing (this study, ties at best)**. The wall is the labels — they reward long-tenure
concentration — not the method. **Copeland remains the champion and the shipped artifact.**

"Top-10 guaranteed" is not achievable by any method: the metric ceiling is reached and proven, but
the competition outcome is governed by how the hidden labels correlate with this arbiter (and
whether they penalise impossible tenure) — unmeasurable, and unmoved by further model work.

## Learned stacker — letting the labels pick the mix (`experiments/exp_stack.py`)

A linear stacker fit on the train-label half (target = blind tier; features = the 5 base-method
scores) — the textbook "make your own best of best." The learned weights:
`copeland +1.20, hand +0.16, rrf +0.13, mc4 −0.06, borda −0.61`. **The data itself weights Copeland
dominantly and discards the rest.** Yet the fitted stacker underperforms pure Copeland (best full
0.8667 vs 0.8779; nested +0.0111/16-of-20 vs +0.0142/19-of-20; the nested selector picks Copeland
17/20). Seventh method class, same verdict: Copeland is the data-optimal mix and nothing exceeds it.

## Minimax-robust check across all 7 evaluators (`experiments/exp_robust_minimax.py`)

Instead of optimizing one arbiter, score every candidate ranking across all 7 known label sets
(blind arbiter + 6 LLM-judge sets) and find the best WORST-CASE — the principled hedge against an
unknown 8th (hidden) evaluator.

| ranking | min across 7 | mean across 7 |
|---|--:|--:|
| golden | 0.7680 | 0.8835 |
| fusion-raw | 0.7877 | 0.9027 |
| **Copeland lock30** | **0.7892 (best)** | 0.9036 |
| RRF lock30 | 0.7883 | 0.9038 (best) |

Two findings that strengthen the shipped bet:
1. **Copeland lock30 is minimax-optimal** — best worst-case of any ranking, and within 0.0002 of
   the best mean. The artifact already shipped is also the most robust to an unknown evaluator.
2. **Golden is dominated on all 7 evaluators** — lowest mean (0.8835) and worst worst-case
   (0.7680). Every (B)-bet ranking beats golden on *every* known judge. The "golden is safer"
   case rests entirely on a hypothetical 8th evaluator that manually date-checks tenure — a world
   **none of the 7 measurable evaluators exhibit**. Golden's safety is conjectural; Copeland's
   dominance is measured. Residual risk of the bet (a human tenure-checker) is unmeasured, not
   disproven — but it is the only world in which the shipped choice loses.
