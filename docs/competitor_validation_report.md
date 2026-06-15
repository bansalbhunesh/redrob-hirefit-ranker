# Competitor & Technique Validation Report

**Question this answers:** of everything the field (and the literature) does that we don't,
*which innovations are genuine and which are honeypots* — techniques that inflate a proxy
leaderboard, exploit a saturated metric, overfit synthetic labels, or leak the benchmark,
without improving true ranking quality? Every claim below is cross-verified against our
blind-label framework with a fixed strict-evaluation battery; competitors are referred to
by technique and by anonymous index (C1…C6 = the submissions ranked at/around ours on the
blind proxy), never by name. Golden submission (`af8f2b32`) untouched throughout.

---

## 1. The strict-evaluation battery (our defensible validator)

A single blind-set number is not evidence. Every technique and every competitor lead is run
through four tests; a "win" must survive all four to count.

| test | what it catches | implementation |
|---|---|---|
| **Nested repeated-holdout** (R=20–50) | single-split overfit; hyperparameter cherry-picking | re-select strength on each split's train half, score its untouched test half |
| **Cross-label consistency** | proxy/benchmark overfit; synthetic-label leakage | re-rank on 7 independent judge-graded label sets; a real lead keeps its place |
| **Repeated-holdout significance** | "lead" that is inside the noise band | bootstrap the blind labels; report P(challenger > incumbent) |
| **Proxy-inflation diagnostic** | leaderboard gains driven by honeypot promotion | flag composition (anachronism / disqualifier) of the candidates a method promotes |

This battery is itself the contribution: it is what separates a genuine improvement from a
metric mirage, and it is reproducible (`experiments/*.py`, deterministic).

## 2. The competitive landscape is real but *saturated*

On the 100K blind arbiter we are **#4 of 38 scored submissions**, inside a **0.006-wide top
cluster** (#1 = 0.8658, us = 0.8625, #5 = 0.8599). The instinct is "three teams beat us —
copy them." The battery says that instinct is wrong.

**Finding 2a — the top submissions pick *different* candidates and score the same.** Pairwise
overlap of each top submission with our top-100 is only **50–55/100** (Jaccard 0.33–0.44).
Half-different selections land within ±0.003 composite. The proxy cannot distinguish them:
near the top it is **flat/saturated**, so many distinct top-100s are scored equivalently.

**Finding 2b — the leaderboard order does not survive independent labels.** Re-ranking the
8 submissions on 7 independent judge sets, our rank swings between **#2 and #6**, and the
blind-set #1 (C1) falls behind others on `merged_j2`/`merged_j3`. **No submission holds a
stable lead across label sets** — the ordering is an artifact of *which* proxy you score on.

**Finding 2c — the leads are not statistically significant.** Bootstrap (R=50) of the blind
labels, P(challenger > us):

| submission | blind composite | P(> us) on resamples | verdict |
|---|---|---|---|
| C1 (blind #1) | 0.8658 | **11/50** | not significant — we win 78% of resamples |
| C2 | 0.8649 | 14/50 | not significant |
| C3 | 0.8639 | 20/50 | not significant |
| C4 | 0.8599 | 9/50 | not significant |
| C5 / C6 | 0.8482 / 0.8003 | 19/50 / 5/50 | not significant / behind |
| **our fusion-raw** | **0.8753** | **46/50** | **robust** (only submission with a real edge) |

**Conclusion of §2:** the teams "ahead" of us have **no genuine, transferable, or significant
advantage** — their +0.001…+0.003 edges are proxy-overfit noise on a saturated metric. This
is the field-level honeypot: *the leaderboard itself*. Chasing +0.003 is chasing noise.

## 3. Technique-by-technique verdicts (genuine vs honeypot)

Each is the strongest version of a class the field/literature pushes, tested under the battery.

| technique (class) | best superficial result | under the battery | verdict |
|---|---|---|---|
| **Top-K cross-encoder rerank** (the field's most-hyped weapon) | in-sample +0.014 composite | holdout **−0.016**; strength unselectable from train | **Honeypot** (single-split mirage) |
| **LambdaMART / LTR** (incl. *trained on the blind labels themselves*, NDCG@10 objective) | strong on a curated sample | leak-safe holdout **−0.040…−0.104** NDCG@10 | **Honeypot** (overfit; loses even with label access) |
| **Learned linear / logistic weights** | fits the labels | **0.824 vs 0.881** composite | **Misleading** (worse than hand-tuned) |
| **Learned interaction features** | single split +0.008 | 20× holdout → **noise** (best +0.005, 14/20) | **Misleading** |
| **Static dense / semantic embeddings** (offline) | — | **+0.0000** NDCG@10 at ~2.2× runtime | **Genuine technique, empty here** |
| **Test-time-training reranker (DART, ACL'26)** | replicated **above** its paper (+5.3% vs +2.1% on dense) | composite **−23% rel** vs hand | **Genuine paper, wrong substrate** (adapts weak dense repr.) |
| **New orthogonal features** (quantified-impact density; gzip-NCD) | flickers positive at some weights | no train-selectable blind gain | **Empty** (feature set already comprehensive) |
| **Rank-space fusion** (RRF/Borda + top-lock) | nested **+0.0108**, NDCG@50 +0.043 | clean variant **−0.0322**; raw gain is 100% anachronism-promotion | **Conditional** (see §4) |
| **Graph reranking** (cosine k-NN + score propagation) | single-split **+0.0272** | nested R=20 → **+0.0053, 12/20**; exposure 52→61 | **Honeypot** (collapses under resampling; inflation-driven) |

Pattern: **every model/trick that beats the hand scorer on one split is killed by nested
resampling or cross-label checks.** The genuine techniques (dense, DART) are real methods
that are simply *empty on this task* because the bottleneck is feature information content,
not the model class. The bottleneck conclusion now holds across **score space, rank space,
and graph space**.

## 4. The one place a real signal hides — and why it's a *bet*, not a free win

Rank-fusion (#13) and graph-smoothing both gain on the proxy *only* by promoting the
"impossible-tenure" (anachronism) candidates our integrity guard demotes. The natural read is
"proxy inflation — reject." But the data complicates that:

- Population-wide, anachronism-flagged candidates are **~80× more likely to be tier-5**
  (mean tier 3.0 vs 0.6); **7/7 independent judge sets reward them**; our own golden top-100
  is already **52% anachronism**. By *every label we can measure*, they are strong.
- So `fusion-raw` (which leans in) is the **only** submission with a robust proxy edge
  (+0.0135, 46/50) and it tops the independent sets too.

Two interpretations, separable only by the hidden human labels:
- **(B) Trust the arbiter** → these are genuinely strong; `fusion-raw` is a real +0.0128 gain
  and we (and the field) are *under-promoting* them.
- **(A) They are planted honeypots** whose only tell (a tenure longer than the tech has
  existed) is caught by careful *humans* but by no automated label or LLM judge → golden's
  caution is a structural edge. Every measurable signal looks like (B) even if (A) is true.

This is the genuine, irreducible strategic fork. It is also where **we are likely *more*
right than the field**: no other submission appears to even detect this class (their exposure
is 47–63/100 with no evidence of deliberate handling), so whichever way the hidden rubric
falls, we are the only team positioned to *reason about it on purpose*.

## 5. Where competitors are likely wrong

1. **Treating the blind-proxy rank as ground truth.** It is saturated and non-transferable
   (§2). Optimizing to climb it past ~0.86 is optimizing noise.
2. **Shipping single-split "wins"** (cross-encoder, LTR, graph). Without nested/cross-label
   gating these look like gains and are not — the field almost certainly ships several.
3. **Unwitting honeypot exposure.** They carry 47–63% anachronism candidates with no sign of
   a deliberate decision; they are taking the (B) bet without knowing they are betting.
4. **Complexity without evidence** (torch rerankers, dense pipelines) that breaks the offline/
   deterministic guarantees for no measured ranking gain.

## 6. Evidence-backed roadmap (highest-probability path to win)

1. **Do not chase the proxy.** It is empty (13+1 measured negatives) and saturated (§2). No
   model/trick lever remains in score, rank, or graph space.
2. **Ship golden as the low-variance floor** (`af8f2b32`) — it is statistically tied with the
   "leaders" and beats most of them on resamples, with full offline/deterministic guarantees.
3. **Hold `fusion-raw` as the high-EV option** (validated, on disk, golden untouched): the
   only robustly-better-than-golden ranking on every measurable label. Deploy it *iff* we
   decide to take the (B) bet (trust the arbiter). This is the single highest-leverage
   decision available and it is a *risk call*, not a technical gap.
4. **Win the human-judged stage on defensibility, not metric.** The differentiators no
   competitor has: (a) this validation battery and the measured-negatives ledger — scientific
   rigor a human reviewer can verify; (b) the anachronism analysis — being the only team that
   can *explain* the honeypot axis rather than stumble into it.
5. **Stop adding features.** The feature set is comprehensive (two independent new features
   added nothing). Effort should go to the (A)/(B) decision and the defense narrative, not a
   15th reranker.

## 7. Reproduce
`experiments/_competitor_extract.py` (disk-safe top-100 extraction),
`competitor_anachronism_audit.py` (exposure vs composite),
`competitor_stress_test.py` (overlap + cross-label + bootstrap significance),
`exp_graph_rerank.py` (graph honeypot), plus the rank-fusion suite (`exp_rankfusion*.py`)
and the measured-negatives ledger (`docs/measured_negatives.md`, `rank_fusion_study.md`).
