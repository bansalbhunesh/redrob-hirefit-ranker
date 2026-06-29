# Universal Frontier V6 Experiment

## Decision

Keep the exact V5 ranking and ship only quality-safe inference hardening on
`codex/universal-frontier-v6`. V6 is a Pareto improvement in implementation:
same candidates, ranks, scores, reasons, evaluator metrics, and integrity
behavior; less repeated CPU work in two inference hotspots. It is not presented
as a new accuracy model.

## Ranking search

The search used 35 generic candidate features, 15 development label families,
pairwise logistic heads, robust lower-quartile aggregation, group-DRO variants,
and local rank fusion. Reviewer and blind-recruiter labels were then removed
from training entirely and retained only as unseen validation.

The no-human-label sweep produced 2,284 settings that improved or tied all 60
full-table component cells. That encouraging in-sample count did not survive the
stronger selection protocol:

- Five candidate-level cross-fit folds scored every candidate with models that
  had not seen that candidate's labels.
- The cross-fitted sweep produced 6,129 distinct orders and only seven
  all-component survivors.
- Each survivor was retrained on all non-human labels and then tested 13 more
  times, leaving one training family out on every pass.
- The only candidate with zero losses in the full fit and every leave-one-family-
  out run was the identity order: V5 itself.

The strongest cross-fitted challenger raised H2 from 0.884206 to 0.884347,
mean-15 from 0.910406 to 0.910489, and reviewer from 0.809768 to 0.809871 while
blind stayed tied. After the final full fit it lost one component; across the
leave-one-family-out tests it accumulated 14 component losses. It was rejected.

This is the central V6 finding: apparent gains were real on the observed table
but not stable enough to call universal. Shipping them would overfit the
measurement system.

## Performance changes retained

Two exact arithmetic refactors survived isolated A/B tests:

1. V2 and the main-score feature used by V3/V4/V5 are accumulated in one pass.
   The result is bit-for-bit equal to calling both scorers separately. On a real
   5,000-candidate feature set, median isolated time fell from 0.0546 s to
   0.0345 s (36.8%).
2. The V3 model's 3,000-row feature matrix converts artifact feature names once
   and computes derived values once per candidate. The matrix is bit-for-bit
   equal; median isolated time fell from 0.1848 s to 0.0425 s (77.0%).

Two broader retrieval fusions were measured and reverted. Returning text plus
BM25 statistics increased a 20K Docker run from 22.2 s to 66.4 s. Returning
compact statistics while rebuilding text later moved a profiled 5K run from
23.1 s to 24.1 s. Neither is present in V6.

## Full verification

The hardened image completed all 100,000 candidates with `--cpus=2
--memory=16g --workers 2` in 197.2 s pipeline time. Sampled peak memory was
4,204.5 MiB. It detected all 53 honeypots, emitted none, and produced the exact
V5 SHA-256:

`8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`

Docker Desktop exposed only about 7.6 GiB from its VM despite the 16 GB
container request; the measured peak stayed comfortably below that effective
cap. The adjacent unchanged-V5 control took 299.2 s under severe host load,
while earlier V5 runs were 199.0-209.4 s. Therefore the full-run evidence proves
no regression and exact reproduction, not a defensible 34% universal speedup.

Final suite: 225 collected, 219 passed, 6 environment skips.
