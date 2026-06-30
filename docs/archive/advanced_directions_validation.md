# Advanced Directions — validation under the strict framework

A post-fusion brief proposed 8 advanced directions (AcuRank, weighted RRF, ConFit mining,
teacher distillation, SPLATE, dependence-aware judges, conformal gates, dual-head) with
claimed proxy gains of +0.002…+0.020. Each is dispositioned here against the blind arbiter
and the strict gates. Golden (`af8f2b32`) untouched; full suite green.

## Two premises in the brief that the evidence contradicts

The brief builds on two claims that this session's measurements refute. Correcting them
first, because several directions inherit the error:

1. **"Fusion beats golden on all 7 label sets — a proven win."** The 7 label families are
   **~1.9 effective independent judges** (mean pairwise Spearman 0.67; `merged_j*` 0.92–0.93),
   and **56% of the +0.0128 gain is carried by 5 candidates**, inverting to −0.011 without the
   anachronism class. It is a fragile, low-independent-evidence, anachronism-driven effect —
   **not** a robust proven win (`evidence_channels_study.md`, Exp 6/8).
2. **"The honeypot detector is over-aggressive; the dates are synthetic noise (false
   positives)."** This asserts interpretation **(B)** as fact. It is the irreducible (A)/(B)
   fork — every automated label looks identical under both — resolvable only by the frozen
   human integrity panel (`golden_vs_fusion_decision.md`). Asserting (B) pre-judges the one
   open question.

## Disposition of the 8 directions

| # | direction | status | result |
|---|---|---|---|
| 8 | **Dual-head graded integrity** (P0 centerpiece) | **TESTED — refuted** | −0.1105 (nested −0.1272, 0/20). See below. |
| 2 | **Correlation-aware weighted RRF** | **TESTED — refuted** | −0.0706 vs equal-RRF −0.0323 (both 0/20). Weighting by "1−max-corr" upweights `bm25` (independent because near-useless) and downweights `hand` (the real signal): independence ≠ value. |
| 3 | ConFit disagreement mining | **already built** | the frozen 178-candidate disagreement lockbox (`disagreement_set/`, hash e36c96ac) *is* this asset. |
| 6 | Dependence-aware judge aggregation | **already done** | n_eff = 1.85/7 computed (Exp 6). Reweighting judges does not create a tuning lever — the weight-learning lever is measured-negative #2. |
| 1 | AcuRank adaptive (TrueSkill) computation | **not a proxy lever** | adaptive computation changes *efficiency*, not ranking quality; runtime is already ~90 s < 300 s, and there is no holdout-positive channel to allocate compute to. |
| 7 | Conformal promotion gates | **confirms golden** | "promote only if confident" with a 5-candidate-fragile gain ⇒ the gate rejects nearly all promotions and reverts to golden. A conservative gate cannot manufacture a gain. |
| 5 | SPLATE / CPU late interaction | **out by constraint** | needs static token embeddings + a SPLADE projection (torch-class deps + download); measured-negative #1 already showed static `potion-32M` embeddings are flat at NDCG@10; disk at 97%. |
| 4 | Offline LLM-teacher distillation | **pending budget; low prior** | needs paid LLM calls (~$10–20); the distilled output is a learned-weight feature, blind-gated like measured-negative #2 (which lost). Not run without explicit approval. |

## Dual-head, in detail (the brief's highest-confidence claim)

Reconstructing quality = `final_score / honeypot_multiplier` and re-applying a **graded**
integrity head (hard→0, anachronism→g_anach, softened→g_amb, clean→1.0), reranking all 100K:

| g_anach | g_amb | composite | Δ golden | |
|---|---|---|---|---|
| 1.00 | 0.05 | 0.8625 | +0.0000 | = golden (sanity ✓) |
| 1.00 | 0.40 | 0.8625 | **+0.0000** | rescue ambiguous only |
| 0.50 | 0.40 | 0.7520 | −0.1105 | soft-penalize anachronism |
| 0.30 | 0.40 | 0.7520 | −0.1105 | **dual-head proposal** |
| 0.00 | 0.40 | 0.7520 | −0.1105 | hard-exclude anachronism |

Class counts over 100K: anachronism **289**, ambiguous **31**, hard 22, clean 99 658.

Two findings refute the proposal:
1. **The baseline was inverted.** The brief frames dual-head as grading anachronism "0.3–0.4
   instead of 0.0," i.e. a *recovery*. But golden does not detect anachronism at all — those
   candidates already sit at integrity **1.0** in golden's top-100. So every grade <1.0 is a
   **demotion**, costing −0.11; there is nothing to recover. (Once the penalty is enough to
   push them past the top-100 cutoff, 0.5/0.3/0.0 are identical.)
2. **The one genuine lever does nothing.** Rescuing the softened/ambiguous class
   (0.05→0.40) yields **+0.0000** — there are only 31 such candidates in 100K and none are
   competitive for the top-100 even when rescued. Golden buried them correctly *on quality*,
   not on integrity.

So dual-head is not a free lunch; it is the same (A)-bet as constrained fusion (−0.11 on the
proxy), with the proxy cost incurred the moment anachronism is penalized at all.

## Net

Every direction is already-done, refuted under strict testing, out by hard constraints, or a
conservative gate that merely re-confirms golden. **No advanced direction produces a robust
proxy gain**, and the two that looked most promising on paper (dual-head, weighted RRF) fail
for instructive reasons — inverted baseline and independence≠value, respectively. The
information-architecture and ensemble levers are exhausted on the proxy; the decision is
unchanged: **ship golden**, and let the frozen human integrity panel decide whether the
anachronism class is genuine (B) or planted (A). The reusable assets here — disagreement
lockbox, dual-head decomposition, judge-dependence numbers — are Stage-4/5 *defense*, not
metric levers.

Reproduce: `exp_dual_head.py`, `exp_weighted_rrf.py` (+ `exp_audits.py`,
`evidence_channels.py` from the prior phase).
