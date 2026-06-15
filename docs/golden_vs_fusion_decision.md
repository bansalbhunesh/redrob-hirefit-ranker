# Golden vs Fusion — the ship decision, on one page

Three submissions are on disk; **golden ships**; the others are validated contingencies.

> **Terminology correction (precise denominators).** Where this and related docs say golden's
> top-100 contains "52 honeypots," the exact meaning is: **52 candidates flagged by our
> separate *anachronism* detector** (a claimed tech tenure longer than the technology has
> existed), located **inside golden's top-100**. By the **shipped** honeypot detector
> (`features.py`), golden's top-100 has **0** flagged candidates — both statements are true of
> *different* detectors. The 52 are **detector-flagged anomalies**, NOT **confirmed hard
> contradictions** (no ground truth has confirmed them) and NOT **confirmed official planted
> honeypots** (the ~80 planted IDs are not in our possession; overlap is unmeasured). These
> three categories are not interchangeable; resolving which the 52 truly are is the object of
> Experiment Ψ (`experiment_psi_human_calibration.md`).

| submission | blind composite | robust vs golden? | hard honeypots in top-100 | when it is the right ship |
|---|---|---|---|---|
| **golden** (`af8f2b32`, shipped) | 0.8625 | — | 52 | default; EV-max absent evidence either way |
| **fusion-raw** (`experiments/fusion_raw_submission.csv`) | **0.8753** | yes (+0.0135, 46/50; ahead on 7/7 label sets) | 62 | **world (B)**: trust the arbiter — the flagged candidates are genuinely strong |
| **constrained** (`experiments/constrained_submission.csv`) | 0.7314 | no (−0.144, 0/20) | **0** | **world (A)**: the flagged candidates are planted honeypots a human panel will zero out |

## The single fork everything reduces to

The flagged ("impossible-tenure") candidates are **top-tier by every label we can measure**
(blind mean tier 3.0 vs 0.6 population-wide; rewarded by 7/7 independent judge sets) — yet
their tenure claims are temporally **impossible**. Two mutually exclusive worlds:

- **(B) Genuine.** The labels are faithful; these are strong engineers with one sloppy field.
  → `fusion-raw` is a real +0.0128 win; golden under-ranks them; constrained is self-harm.
- **(A) Planted honeypots.** The dataset planted attractive-but-impossible profiles; the
  blind/LLM labels (which never date-check) all fall for them; only a careful human catches
  the tell. → `constrained` (0 honeypots) is the only safe ship; golden/field carry 52–63 traps.

No proxy can separate (A) from (B): by construction every automated label looks identical in
both worlds. **Only the frozen human integrity panel** (`disagreement_set/`, hash
`e36c96ac66cffa02`, 178 candidates, Q2 = "decisive impossible contradiction?") resolves it.

## Decision rule (pre-registered, before the panel returns)

1. **Default: ship golden.** It is statistically tied with the field's "leaders" (which beat
   us only 9–20 times in 50 bootstrap resamples) and keeps every offline/deterministic
   guarantee.
2. **If the panel says Q2-yes is rare** among flagged candidates (they read as genuine, world
   B) → switch to **fusion-raw** for the measured +0.0128 and the cross-label lead.
3. **If the panel says Q2-yes is common** among flagged candidates (decisive contradictions,
   world A) → the blind composite is compromised on this axis; switch to **constrained** and
   make the zero-honeypot integrity argument the centrepiece of the Stage-4/5 defense.

All three are reproducible; golden is byte-identical and untouched (`af8f2b32`). The decision
is a one-line submission swap, made *after* evidence, not before.
