# Integrity-Constrained Rank Fusion — study & shipping decision

**Thesis.** Earlier work showed (a) unconstrained rank fusion gains +0.0128 on the blind
arbiter *only* by promoting "impossible-tenure" (anachronism) candidates, and (b) those
candidates are top-tier by every label we can measure. That left one irreducible fork:
are they **genuine** (B) or **planted honeypots** (A)? This study does not pretend to
resolve that from proxies. It instead builds the architecture that is *correct under (A)*
— a two-level integrity gate with hard-exclusion and evidence-gated ambiguous rescue — and
quantifies exactly what it costs if (B) holds, then freezes the one experiment that can
actually decide it. Golden (`af8f2b32`) is untouched throughout.

## 1. Two-level integrity classification (`experiments/integrity2.py`)

The shipped scorer treats honeypots with a single blunt multiplier (0.0× hard, 0.05× for
two "softened" classes). That conflates *decisive impossibilities* with *innocent
incomplete records*. We split every flag:

| level | rule | rationale |
|---|---|---|
| **HARD** (never rescued) | `experience_timeline_exceeds_claim`, **`tech_anachronism`** (tech claimed longer/earlier than it existed), `impossible_education_timeline`, `multiple_current_jobs` (>2), `expert_skill_zero_duration` *uncorroborated*, `summary_profile_contradiction` | a temporal/logical impossibility; no amount of relevance should rescue it |
| **AMBIGUOUS** (rescue-eligible) | `career_history_too_short_for_claimed_yoe`, `expert_skill_zero_duration` *corroborated in career text/assessment* | an innocent data-entry / abbreviated-import reading exists |

The decisive addition over the shipped detector is **`tech_anachronism`** — the shipped
scorer does **not** detect it, which is exactly why golden's top-100 carries 52 such
candidates. Reclassifying the top-3000 pool: **137 HARD (all anachronism), 0 ambiguous,
2863 clean** — the other hard/ambiguous classes never reach the rankable pool because the
shipped multipliers already removed them. So in practice the constraint that matters is
**hard-excluding anachronism**, plus rescuing ambiguous candidates the shipped 0.05× buried
*below* the pool.

## 2. The constrained pipeline (`experiments/exp_constrained_fusion.py`)

5 **complementary** channels (not five weightings of one scorer): tuned composite, lexical
BM25, production-evidence, semantic/HyRE, career-quality → **RRF + Borda** consensus →
**hard-integrity exclusion** → ambiguous rescue (entry only with ≥2 channels + strong
production evidence + no hard contradiction) → **top-10 lock (clean hand) + ranks 11–50
fusion** → top 100.

## 3. Results — the integrity gate works; the proxy cost is severe

| metric | golden | fusion-raw (unconstrained) | **constrained** |
|---|---|---|---|
| blind composite | 0.8625 | 0.8753 | **0.7314** |
| hard honeypots in top-100 | 52 | 62 | **0** |
| hard honeypots in top-10 | (several) | — | **0** |
| nested R=20 vs golden | — | +0.0135 (46/50) | **−0.144 (0/20)** |

The constrained submission loses on the blind arbiter **and on all 6 independent judge
sets** (−0.08 … −0.14). This is *not* a tuning failure: no RRF constant, top-lock depth, or
Borda weight can recover it, because the excluded 52 candidates are the highest-tier ones in
the pool and are simply no longer available. **The composite cost is the price of refusing
to rank any temporally-impossible profile.**

This sharpens the fork to its starkest form:
- **If (B)** (anachronism candidates are genuine): constrained fusion is catastrophic
  (−0.13) — it discards the best people.
- **If (A)** (they are planted honeypots): constrained fusion is the *only* submission that
  does not get gutted when the traps are revealed; golden carries 52 and the field 47–63.

## 4. Honeypot-count cross-verification (`experiments/_hardcount_100k.py`)

The official challenge plants **~80** honeypots. A calibrated *hard* detector should flag a
number of that order, not a slice of the dataset. Ours flags **294 / 100 000 = 0.29%**
(117 of them blind-tier-5). Competitor "honeypot" counts reported in audits — **7 580 /
16 157 / 55 942 (7.6% / 16% / 56%)** — are detecting generic low quality / weak profiles /
keyword anomalies, **not** the planted traps. Those large counts must **not** be read as
better trap detection; a detector that flags 7–56% of everyone is uninformative about the
~80 planted IDs. Our 0.29% is the right order of magnitude and is *derived from data*
(a temporal contradiction per candidate), not hard-coded IDs.

## 5. The experiment that actually decides it — frozen lockbox

`experiments/build_disagreement_set.py` freezes a **prospective disagreement set** of **178
candidates** (hash `e36c96ac66cffa02`, params frozen *before* any labels), drawn from:
golden-only (39), fusion-only (39), flagged-but-promoted (29), flagged-not-promoted (25),
clean-high-quality (30), rank-boundary 8–20/40–70 (16). A human panel answers two **separate
blind** questions per candidate — (1) job fit for the JD, (2) does the profile contain a
**decisive impossible contradiction** — with rank, selector, detector flag, and all model
labels hidden. The integrity question is what no automated label or LLM judge has answered;
it is the only thing that separates (A) from (B). The reviewer packet is generated blind and
shuffled (`reviewer_packet.jsonl`, gitignored); the manifest (ids + buckets + frozen hash)
is committed as the lockbox record.

## 6. Shipping-gate scorecard

| gate | requirement | constrained fusion |
|---|---|---|
| Official validator | pass | **pass** |
| Runtime | < 300 s | **pass** (~90 s full pipeline; fusion is on the cached pool) |
| Hard honeypots in top-100 | 0 | **0** |
| Hard honeypots in top-10 | 0 | **0** |
| Composite improvement | ≥ pre-registered threshold | **FAIL** (−0.13 on every label set) |
| Leave-one-label-family-out | positive/neutral on every family | **FAIL** (negative on all 7) |
| Prospective human integrity set | positive | **PENDING** (lockbox frozen; needs the panel) |
| Golden baseline | untouched & reproducible | **pass** (`af8f2b32`, 171 tests) |

## 7. Decision

Constrained fusion **does not ship today**: it fails the composite and leave-one-family-out
gates by a wide margin, and the only gate that could justify it — the prospective human
integrity set — is **unresolved by construction** (we have no human integrity labels). The
correct posture is therefore unchanged in *action* but sharper in *understanding*:

1. **Ship golden** — the EV-maximizing choice unless we have positive evidence for (A).
2. **The constrained pipeline is the contingency ship**: if (and only if) the frozen human
   panel returns that the flagged candidates carry decisive impossible contradictions, then
   the blind composite is itself untrustworthy on this axis, the −0.13 is illusory, and the
   zero-honeypot submission becomes correct. The architecture is built, validated, and waiting.
3. **Do not over-detect.** A 0.29% hard rate is the discipline; chasing competitor-style
   7–56% "honeypot" counts would discard real candidates for no benefit.

The scientifically-defensible story for the human panel is now complete on both sides: we can
explain, candidate by candidate, exactly who moves and why under each interpretation.

Reproduce: `integrity2.py`, `exp_constrained_fusion.py`, `_hardcount_100k.py`,
`build_disagreement_set.py`, `build_constrained_submission.py`.
