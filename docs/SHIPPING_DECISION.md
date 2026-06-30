# Shipping Decision — V6 battle-proof release

## Decision

**Ship `codex/universal-frontier-v6` at commit `7525500` plus this final
positioning pass.** The release artifact is the frontier-v5 ranking wrapped in
V6's fail-closed execution and publication envelope.

Golden output SHA-256:
`8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`.

## Why this is the strongest shipping choice

| Decision axis | V6 evidence |
|---|---|
| Versus main | wins 30/30 composites across 15 label families × 2 missing-label policies |
| Broad public quality | #1 / 673 mean7; 0.906553 |
| Strongest-union quality | #1 / 100 mean15; 0.910406 vs best public 0.907475 |
| Balanced public quality | #3 / 322 equal four-axis mean; no four-axis dominator |
| Recruiter slices | reviewer 0.809768; blind 0.905858 |
| Integrity | 53 traps detected; 0 emitted |
| Constrained runtime | 136.0 s pipeline / 149.1 s wall at 2 CPU / 16 GiB |
| Reproducibility | exact input/model/wheel/output hashes; deterministic environment |
| Failure safety | forced 3-GiB OOM preserves prior output and leaves 0 mounted temps |
| Verification | 262 passed, 6 environment skips; 10,000 corrupt outputs and 9,750 invalid configs rejected |

## Why not another fusion

Six of 120 underlying component cells trail main while all 30 composites win.
We tested 883 main/champion safety fusions. Twelve erased every component loss;
all twelve lost all 30 champion composites. There is no free fusion switch.

The right decision is the stronger all-around ranking, with the six small
component tradeoffs disclosed—not a silent near-reversion to main.

## Challenge positioning

The official challenge page publishes mission dimensions but not numeric
weights. Our transparent mission-derived scorecard places V6 at **93.7/100**,
projected **#1** with an honest **#1–#3** range. That is positioning evidence,
not an official score or leaderboard result. See `docs/CHALLENGE_POSITIONING.md`.

## Honest limit

Official hidden labels remain unknown. Specialist public outputs lead individual
axes, and no repository can prove literal invulnerability. V6 is the strongest
measured all-around choice and the most rigorously protected release—not a claim
that the official judging result is already known.
