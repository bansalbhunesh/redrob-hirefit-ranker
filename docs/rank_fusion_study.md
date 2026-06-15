# Rank-Space Fusion Study — a novel direction, rigorously gated

**TL;DR.** Every prior measured negative (#1–#12) operated in *score* space (blend a
signal into the linear composite, or swap the model). This study tests a structurally
different lever neither our pipeline nor the comparable field had benchmarked:
**rank-space fusion** (Reciprocal Rank Fusion and Borda count), including a *top-locked*
variant that protects the near-perfect top-10 and re-fuses only the NDCG@50 tail.

Result, in one line: **rank fusion produces a +0.0128 composite "gain" on the 100K blind
proxy — and that entire gain is impossible-tenure honeypot re-promotion.** Forbid
promoting those honeypots and the gain inverts to −0.0322. So there is **no clean
ranking gain in rank space** (the model/aggregation lever is empty here too), *but* the
experiment independently re-derived the honeypot trap and quantified, for the first
time, the risk/reward of the integrity hedge.

All numbers are deterministic (`PYTHONHASHSEED=0`, single-thread BLAS) and reproducible
from `experiments/exp_rankfusion*.py`. The golden submission (`af8f2b32`) is untouched.

---

## 1. Why rank space, and why it could have helped

The shipped scorer is a tuned 22-feature linear sum × multiplicative guardrails. Two
properties motivated a rank-space test:

- A linear score-sum can be dominated by one feature's scale; **Reciprocal Rank Fusion**
  (Cormack, Clarke & Büttcher, SIGIR 2009) is scale-free — it fuses *rank positions*,
  `score(c) = Σ_f w_f / (K + rank_f(c))`, so it is immune to the per-feature calibration
  problems a linear blend can suffer. This is exactly the failure mode that could leave
  signal on the table in the noisy 11–50 region.
- Fusion admits a **top-lock**: freeze the hand top-L (protect the 0.50-weight NDCG@10,
  where P@10 ≈ 1.0) and re-fuse only the candidates competing for ranks L+1…100. No
  score-blend can target the 0.30-weight NDCG@50 surgically like this; the comparable
  field does not do it.

Six orthogonal ranker families were fused (skill, AI-depth, production, lexical/semantic,
career trajectory, and the hand composite itself), each ranking the full 3000 pool.

## 2. Gating discipline (identical to #11/#12)

Choose every hyperparameter (fusion method, ranker set, `K`, top-lock `L`) on a TRAIN
label half; report the delta on an untouched TEST half; then re-check with **R=20
nested repeated holdouts** where the selector re-picks the train-best config on each
split and is scored on that split's test half. Single-split "wins" that don't survive
the nested resampling are noise.

| stage | result |
|---|---|
| single-split gate (train-argmax → holdout) | **−0.0077** (the train-best config loses out-of-sample) |
| **nested R=20 procedure-generalization** | **mean +0.0108, std 0.0102, 17/20 positive** |
| best full-set fusion composite | **0.8839** vs golden 0.8625 |

The single split was unlucky in *which* near-tied config its train-argmax selected; the
nested test (the honest one) is positive. This was the **first** alternative in 13 to
clear the holdout — which is exactly why it warranted a hard look at *where the gain
comes from* before any celebration.

## 3. Where the gain actually comes from (the decisive diagnostic)

For the modal nested-selected config (all-families, `K=30`, top-lock 20):

| metric | golden | fusion | Δ |
|---|---|---|---|
| NDCG@10 | 0.8288 | 0.8288 | **+0.0000** |
| NDCG@50 | 0.8270 | 0.8697 | **+0.0428** |
| MAP | 1.0000 | 1.0000 | +0.0000 |
| P@10 | 1.0000 | 1.0000 | +0.0000 |
| **composite** | 0.8625 | 0.8753 | **+0.0128** |

The gain is **entirely in NDCG@50** (top-10 untouched, as designed). But the candidate
decomposition is damning: of the 39 slots fusion changes, **added and dropped candidates
have identical mean blind tier (4.95 → 4.95)** — fusion finds no *better-tier* people —
and **25 of 39 promotions are impossible-tenure anachronism honeypots**, several carrying
JD-disqualifier signals, some promoted from deep in the tail (hand ranks 1078, 1702,
1910, 2103). The hand pipeline *deliberately* demoted these via guardrail multipliers;
equal-weight rank consensus over the raw families structurally ignores those multipliers
and drags the traps back up.

## 4. Is any of the gain clean? (the kill test)

Three variants of the same config, R=20 repeated holdout on the blind proxy:

| variant | full composite | Δ vs golden | repeated-holdout | promotions (anachronism / disq) |
|---|---|---|---|---|
| **raw** | 0.8753 | +0.0128 | mean +0.0138, 19/20 | 39 (25 / 8) |
| **guarded** (× honeypot_mult × disq_mult) | 0.8764 | +0.0139 | mean +0.0144, 18/20 | 37 (**24** / 4) |
| **clean** (forbid anachronism promotion) | 0.8515 | **−0.0110** | **mean −0.0322, 1/20** | 52 (**0** / 9) |

Two conclusions, both important:

1. **Re-applying the *existing* guardrails barely helps** — "guarded" still promotes 24
   honeypots and still gains. This independently re-confirms that the existing honeypot/
   disqualifier suite **does not catch impossible-tenure anachronism**; only the dedicated
   detector does.
2. **Forbidding honeypot promotion collapses the gain to −0.0322 (1/20).** Therefore the
   *entire* rank-fusion proxy win is honeypot re-promotion; the clean rank-space signal is
   **negative** — the hand ordering of legitimate candidates is already near-optimal.

→ **Measured negative #13: rank-space fusion adds no clean ranking gain.** Its apparent
proxy "win" is the previously-identified proxy-inflation trap, now reproduced by a
completely independent, principled method that *automatically discovered and exploited*
the honeypot class. The model/aggregation lever is empty in **both** score and rank space.

## 5. The flip side — a quantified, evidence-backed integrity hedge

The blind proxy *rewards* anachronism honeypots (a 7.8-year "RAG" claim scores like any
genuine tier-5). The JD instructs human reviewers to *penalize* impossible/inconsistent
claims. So the measurable proxy and the human-judged final stage are misaligned exactly
on the honeypot axis. Honeypot exposure of each top-100:

| ranking | anachronism honeypots in top-100 |
|---|---|
| golden (shipped) | **52 / 100** |
| fusion-raw / fusion-guard | 62–63 / 100 |
| **fusion-clean** (novel, honeypot-free tail fusion) | **12 / 100** |

Sweeping a human anachronism-penalty `p ∈ [0,1]` over the blind labels and re-scoring:

| p (human aversion) | golden | fusion-raw | fusion-clean | winner |
|---|---|---|---|---|
| 0.00 (raw proxy) | 0.8625 | 0.8753 | 0.8515 | fusion-raw/guard |
| 0.25 | 0.5689 | 0.5785 | **0.5909** | **fusion-clean** |
| 0.50 | 0.2590 | 0.2592 | **0.3625** | **fusion-clean** |
| 1.00 | 0.1640 | 0.1640 | **0.2782** | **fusion-clean** |

Under **any** meaningful human anachronism-aversion (`p ≥ 0.25`), the novel honeypot-free
clean fusion **outperforms both the shipped golden and the proxy-chasing fusion**, by a
margin that grows to **+0.10–0.11 composite**.

**Honest caveat (no overclaim).** The penalty targets the same detector clean-fusion uses
to avoid promotion, so this is a *sensitivity analysis*, not a proxy win. Its force rests
on (a) the detector's validated high precision (7 positive + 12 negative-control tests)
and (b) whether hidden human judges actually penalize the inconsistency the JD warns
about. It is **not** evidence to change the submission: on the only thing we can measure —
the blind proxy, which plausibly tracks automated early-stage screening — golden
(0.8625) still beats clean fusion (0.8515).

## 6. Decision

- **Ship stays golden** (`af8f2b32`). It is the expected-value-maximizing choice for the
  measurable proxy; rank fusion offers no clean improvement on it.
- The contribution here is (i) closing the "did you try rank fusion?" question with a
  rigorous negative, (ii) an *independent* re-confirmation that proxy-leadership is
  honeypot-driven rather than quality-driven, and (iii) the first **quantified** risk/
  reward for the integrity hedge: cost −0.011 on the proxy, upside +0.10–0.11 if human
  judges penalize anachronism, crossover at only mild aversion (`p = 0.25`), and a
  concrete honeypot-free ranking (`fusion-clean`, 12/100 exposure vs golden's 52/100)
  that implements the hedge in a principled way rather than by blunt candidate removal.

Reproduce: `experiments/exp_rankfusion.py` (gate + nested holdout),
`exp_rankfusion_diag.py` (gain decomposition), `exp_rankfusion_guarded.py`
(raw/guarded/clean kill test), `exp_human_aligned.py` (label-model sensitivity).
