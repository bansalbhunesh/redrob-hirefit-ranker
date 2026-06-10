# Generator Forensics — recovering the synthetic pool's latent structure (dev-only)

Companion study to the pre-registered LTR challenger gate (docs/ltr_challenger_gate.md).
Tool: `scripts/generator_forensics.py`; per-candidate features in
`artifacts/forensics_features.jsonl`. Nothing here runs in the ranking path.

## The pool is stratified by construction

Masking numbers in each profile's summary opening exposes the generator's templates:

| stratum (summary template) | size | judge-1 mean tier (249 sample) |
|---|---|---|
| `senior ai engineer with # years` | **21** | 4.71 |
| `senior engineer who has spent the` | **8** | 4.20 |
| `machine learning engineer with # years` | **150** | 4.14 |
| `data scientist / ml engineer with` | **1,000** | 2.40 |
| `software / data professional with #` | **5,000** | 2.00 |
| `software engineer with # years of` | **25,000** | 1.15 |
| `professional with #+ years of experience#` | 63,304 | 0.00 |
| 12 non-target strata (civil eng, HR, sales, ...) | ~405-504 each | 0.00 |

Exactly round strata (25,000 / 5,000 / 1,000 / 150) are deliberate design, and judge
tiers order the strata monotonically: the generator's latent quality variable is, to
first order, *which template you were generated from*, refined within-stratum.

## The gold-strata trap, sprung

The 29 profiles of the two top strata split cleanly when ranked by the shipped system:

- **18 in the top-100** — behavioral multipliers 0.94-1.10, recruiter response rates
  0.61-0.95, almost all open-to-work; judge tiers 4-5.
- **11 excluded (ranks 131-100000)** — every one behaviorally demoted (multipliers
  0.42-0.70): response rates as low as 0.07, 8/11 not open to work. These are the
  planted **"perfect-on-paper but unavailable"** candidates the JD explicitly says to
  down-weight. One (`CAND_0093547`) is a *honeypot wearing the gold template* —
  fabricated timeline (claims 3y, durations 74m), hard-zeroed by the honeypot gate.
- `CAND_0007411` is the audit's known judge-blind-spot case: LLM judge #1 rated it
  tier-5 ("good availability") while its signals read rr=0.12, open_to_work=false —
  the deterministic behavioral layer caught what the surface-reading judge missed.

**Implication recorded before any challenger run:** under a JD-faithful label
hypothesis the shipped top-100 is near-optimal on the gold strata (18/18 available
gold profiles in, all 11 planted traps out). Under an availability-blind label
hypothesis, including the 11 traps would gain — that scenario is exactly what the
pre-registered sweep already measured and declined (docs/sensitivity_sweep.md), and
this study shows *which specific profiles* that decision protects against.

## Planted-fabrication tells (population level)

- 31.1% of profiles self-report tenure in the summary ("with X years of experience").
- Only **12** profiles in 100K inflate the YoE field >3y above their own summary —
  matching the honeypot audit's fabricated-field findings. The tell is planted and
  rare, not noise.

## Use in the challenger

`forensics_features.jsonl` (stated/field/history YoE gaps, company-pool fractions,
stratum signature, expert-zero counts, education tiers) feeds the LTR challenger as
features and drives generator-derived training labels v2. Per the gate, labels v2
never appear on the scoring side.
