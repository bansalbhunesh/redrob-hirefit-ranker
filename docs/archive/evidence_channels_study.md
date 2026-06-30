# Information-Architecture Channels & Robustness Audits

Tests the hypothesis that the remaining lever is not another model but **new independent
evidence channels from structured data**, combined with integrity-/uncertainty-aware
fusion. Deterministic, offline, torch-free. Golden (`af8f2b32`) untouched.

## Scope (what was and wasn't run)

Run here: **Exp 1 BM25F**, **Exp 2 requirement→evidence assignment**, **Exp 3 counterfactual
evidence masking**, **Exp 6 judge-dependence audit**, **Exp 8 influence/deletion audit**
(Exp 5 hard-integrity gate is in `constrained_rank_fusion_study.md`). Not run: **Exp 11
SPLATE** and **Exp 12 ConFit distillation** require torch + model downloads — they break the
offline/deterministic/no-GPU guarantee and the disk is at 97%; out by construction, as for
the earlier dense/cross-encoder classes. **Exp 7/9 conformal/uncertainty** gates were left
unbuilt because they only matter once a channel produces a gain worth gating — none did.

## Exp 1–3: the channels are independent — and they do not move the proxy

Each channel is scored over the 3000-pool and checked for (a) independence from the existing
features and (b) nested-holdout (R=20) lift as a blended signal.

| channel | Spearman vs hand | nested-holdout mean (pos/20) | verdict |
|---|---|---|---|
| **BM25F** (field-aware lexical) | 0.32 | **+0.0008 (12/20)** | independent; **no gain** (noise) |
| counterfactual robustness (1−single-source-dep) | 0.28 | −0.0032 (1/20) | independent; negative |
| requirement coverage (Hungarian) | 0.44 | −0.0090 (6/20) | independent; negative |
| requirements covered (count) | 0.12 | −0.0028 (9/20) | independent; negative |
| weakest mandatory requirement | 0.38 | −0.0287 (3/20) | independent; **clearly negative** |
| evidence-source diversity | 0.26 | −0.0018 (6/20) | independent; negative |
| avg evidence confidence | 0.22 | −0.0095 (7/20) | independent; negative |

**The hypothesis is half-right and the conclusion is sharper than before.** The channels
*are* genuinely independent (correlations 0.11–0.44, not the ~0.9 of redundant rerankers) —
so field structure really does carry information the flattened features don't. **But that
independent information does not predict the blind labels any better.** This is not a failure
to extract signal; it is evidence that the bottleneck is **label-fidelity, not information
architecture**: the proxy rewards tenure/seniority (and, per prior work, impossible-tenure
candidates), which is *orthogonal* to genuine requirement-coverage and evidence-robustness.
A candidate who actually has independent career evidence for every JD requirement does not
score higher on the arbiter than a high-tenure profile that doesn't.

Implication: these channels would help **human-faithful** labels (they measure true job-fit
quality and integrity), and they are first-class **explainability** artifacts — "every JD
requirement has independent, dated career evidence" is exactly the per-candidate justification
a Stage-4/5 human panel can verify. They are not a blind-proxy lever. Fusing them (Exp 4)
cannot manufacture signal from channels that are individually at noise level; the only fusion
effect that survives is the integrity gate (`constrained_rank_fusion_study.md`).

## Exp 6: judge-dependence — "7/7 label sets" is really ~1.9 votes

Pairwise Spearman of the seven label families' gains, mean off-diagonal **0.67**; the three
`merged_j*` sets are near-identical (0.92–0.93). Effective number of independent judges by
eigenvalue participation ratio: **1.85 of 7.**

> The earlier framing "fusion-raw beats golden on 7/7 independent label sets" **overstated the
> evidence.** It is really ~2 independent votes. The cross-label agreement is mostly one
> correlated family, not seven witnesses.

## Exp 8: influence/deletion — the fusion gain is carried by 5 candidates

The +0.0128 fusion-raw gain, decomposed by removing each promoted candidate (backfilled):

| measure | value |
|---|---|
| max single-candidate influence | +0.0019 (**15% of the gain**) |
| **top-5 candidate influence** | +0.0072 (**56% of the gain**) |
| gain without anachronism candidates | **−0.0110** |
| bootstrap R=50 (sign) | 46/50 positive |

Over half the gain rests on **five** promoted candidates, and it inverts entirely once the
anachronism class is withheld. Against the user's own acceptance criterion ("gain not
dominated by a few rows"), fusion-raw **fails**: it is a concentrated, low-independent-evidence
effect, not a broad architectural improvement.

## Net conclusion

1. The information-architecture lever (field structure, requirement→evidence matching,
   counterfactual robustness) yields **genuinely independent** signals that **do not improve
   the blind proxy** — confirming, more deeply than the model experiments did, that the
   bottleneck is label-fidelity.
2. The two audits **downgrade the only apparent win** (fusion-raw) to ~1.9 effective judges
   and a 5-candidate-dependent, anachronism-driven gain — too fragile to displace golden.
3. **Highest-value reuse of this work is defensive, not metric-chasing:** the requirement-
   coverage and evidence-robustness channels are deterministic, explainable per candidate, and
   exactly what a human panel can audit. They strengthen the Stage-4/5 story even though they
   do not raise the proxy.

**Decision unchanged and reinforced: ship golden.** No new evidence channel clears the
acceptance gates; the fusion edge is fragile; the deciding question remains the frozen human
integrity panel (`golden_vs_fusion_decision.md`).

Reproduce: `evidence_channels.py`, `exp_evidence_channels.py`, `exp_audits.py`.
