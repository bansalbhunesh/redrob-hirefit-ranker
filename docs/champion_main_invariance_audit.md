# Champion versus Main — Exhaustive Invariance Audit

## Verdict

Keep `frontier-v5` as the ranking champion and V6 as its hardened release path.
The champion beats the committed main artifact on all 30 composites: 15 label
families under both `exclude` and `zero` missing-label policies. V6 also
reproduces the historical main scorer byte-for-byte, so the hardening does not
change main when main is explicitly selected.

This is strong evidence, not literal invulnerability. Official hidden labels,
unknown future inputs, operating-system failure, and hardware faults remain
outside what a repository can prove.

## Quality matrix

The exhaustive matrix contains 150 cells: 15 label families × two missing-label
policies × five metrics.

The external reviewer source is pinned to Sifter commit
`57c2f74541a02cb8bfd64b358e76d628c9703501`; the combined reviewer CSV SHA-256
is `68764999a03aba32659cf02aad4b6e8214e897449c508d4a4bcad6ae5ab50b47`.
Every other label input hash is recorded in the machine-readable report.

| Metric | Wins | Ties | Losses |
|---|---:|---:|---:|
| Composite | **30** | 0 | **0** |
| NDCG@10 | 19 | 7 | 4 |
| NDCG@50 | 29 | 0 | 1 |
| MAP | 22 | 7 | 1 |
| P@10 | 4 | 26 | 0 |

The six component losses are transparent:

- H2 NDCG@10: −0.000401 under each policy.
- Independent NDCG@10: −0.000425 under each policy.
- `zero`-policy expand MAP: −0.013953.
- `zero`-policy silver20k NDCG@50: −0.004432.

Every affected label family still has a higher champion composite. These are
weighting tradeoffs, not hidden average regressions.

## Can a main/champion fusion erase the six losses?

We evaluated 883 auditable variants: main/champion prefixes, reciprocal-rank
fusion at four constants and 101 weights, linear rank blends, and main-ordered
bands. Twelve variants matched main on every component. All twelve lost all 30
champion composites. No variant was both component-safe versus main and
composite-safe versus the champion.

Therefore the six small dips cannot be removed by a simple safety switch. The
honest decision is to retain the much stronger champion rather than silently
revert most of it to main.

## Main non-degradation

Fresh full-100K Docker executions produced:

| Code path | SHA-256 |
|---|---|
| origin `main` at `7edb29b` | `af8f2b327f05d30e…` |
| V6 with explicit `--scoring-profile main` | `af8f2b327f05d30e…` |

The hashes are identical. Runtime differed because Docker Desktop host load was
high (347.5 s control, 165.0 s V6); no speed claim is inferred from that pair.

## Release and failure matrix

| Test | Result |
|---|---|
| V5 release, two workers | 109.9 s; exact champion hash |
| V5 release, one worker | 135.0 s; exact champion hash |
| fresh hash-pinned image | 131.7 s; exact champion hash |
| 3 GiB forced OOM | exit 137; pre-existing output remained exactly `sentinel` |
| model corruption | rejected by SHA-256 before full scoring |
| invalid/truncated/experimental release configuration | rejected before publication |
| partial write | temporary file removed; prior output preserved |

The final battle-proof rerun moved long-running work to container-local storage:
the repeated 3-GiB OOM preserved `sentinel` **and left zero mounted temp files**.
The post-fix 2-CPU/16-GiB release completed in 136.0 s pipeline / 149.1 s wall
with the exact champion hash.

The base image is digest-pinned. All four production wheels now carry exact
SHA-256 hashes and Docker installs them with `pip --require-hashes`. `pip-audit
2.10.0` reported no known vulnerabilities for the exact four-version production
set on 2026-06-30.

Machine-readable evidence:

- `experiments/champion_main_exhaustive_results.json`
- `experiments/main_champion_safety_fusion_results.json`
- `experiments/champion_invariance_audit_2026-06-30.json`
