# V6 battle-proof release audit — 2026-06-30

## Verdict

The ranking is frozen: this hardening pass changes no scoring weights, candidate
membership, or order. It closes release-engineering gaps around source identity,
configuration types, malformed records, output validation, and forced termination.
The final artifact remains byte-identical:
`8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`.

## Closed gaps

- Pin the exact 100K `candidates.jsonl` SHA-256
  (`de7b8cae39a9f9378a2cd4f8153bfc1f84960bce0ae520f263423d129df4b335`)
  before any ranking work.
- Reject release runs when Python hash or BLAS/thread settings can introduce drift.
- Verify the runtime backend is actually `bm25s`, not merely requested as BM25s.
- Reject Boolean, fractional, non-finite, empty, and wrong-typed programmatic settings.
- Reject non-object JSON records and non-array `.json` roots with explicit errors.
- Require every output score, string reasoning, and exact row-position/rank alignment.
- Rank in container-local temporary storage; touch the mounted output directory only
  during the final verified atomic publish.

## Attack results

| Attack/gate | Result |
|---|---|
| Full test suite | 262 passed, 6 environment skips |
| Deterministic mutation sweep | 10,000 / 10,000 corrupted submissions detected |
| Invalid configuration sweep | 9,750 / 9,750 rejected |
| Tampered candidate file in Docker | exit 1 before ranking; old output preserved; 0 temps |
| `OPENBLAS_NUM_THREADS=2` override | exit 1 before ranking; old output preserved; 0 temps |
| Simulated write/copy/interruption failures | old output preserved; temporary files cleaned |
| Forced Docker OOM, 2 CPU / 3 GiB | exit 137, OOM confirmed; old output preserved; 0 mounted temps |
| Production Docker, 2 CPU / 16 GiB | 136.0 s pipeline / 149.1 s wall; exit 0; no OOM |
| Production output | 100,000 ranked, 53 traps detected, 0 emitted, exact golden SHA-256 |
| Dependency audit | no known production dependency vulnerabilities |

The 3-GiB OOM test initially exposed one empty mounted temp left by SIGKILL. Moving
the long-running work artifact to container-local storage closed it; the repeated
OOM test left zero output-directory temps.

## Honest boundary

No software can be literally invulnerable to every unknown platform or future
dependency defect. This audit proves the controllable release path fails closed
under the tested corruption, configuration, filesystem, deterministic-runtime,
and memory-pressure failures. Hidden-label ranking uncertainty remains a quality
boundary, not a release-integrity gap.
