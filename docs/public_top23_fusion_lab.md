# Public Top-23 Fusion Lab

Date: 2026-06-28. Branch: `codex/top23-fusion-lab`.

## Scope and clean-room rule

GitHub discovery found 1,256 non-empty public Redrob/India Runs repositories and
656 repositories with a valid public 100-row ranking. The 23 public artifacts
ahead of `main` on the frozen H2 proxy were used as research evidence. The five
strongest available repositories were cloned separately for inspection:

1. `soy-praveen/redrob-ranker`
2. `HarshwardhanBhaskar/india-runs-challenge`
3. `candyflipgit/redrob-candidate-ranker`
4. `ragucreation/india-runs_data_ai`
5. `roug047/India_runs_data_and_ai_challenge`

The apparent third-place repository from the live scan became unavailable and
was excluded. No competitor code, candidate IDs, paragraph fingerprints, model
artifacts, or weights were copied into HireFit. Only recurring design ideas
were translated onto features that already existed in HireFit.

## Recurring ideas

- Read career evidence, not just the declared skill list.
- Give direct ranking/retrieval delivery evidence more weight.
- Treat experience-band, seniority, and location as real fit dimensions.
- Apply behavior as a gentle multiplier; do not let an assessment or activity
  signal overwhelm job relevance.
- Keep honeypot and integrity failures as multiplicative gates.

The opt-in `top23-clean` profile therefore multiplies the existing weights for
IR evidence by 1.5, experience-band fit by 2.0, location and senior-title
evidence by 1.5, halves generic core-skill weight, removes assessment score from
rank, and compresses the existing behavior multiplier with exponent 0.35.

## Full 100K result

The real full-pool run used two CPU workers, completed in 212.7 seconds, found
53 guarded profiles, and placed zero guarded profiles in the output.

| Evaluation source | `main` | `top23-clean` | Delta |
| --- | ---: | ---: | ---: |
| H2 availability-blind proxy | 0.8748 | 0.8777 | +0.0028 |
| Independent heuristic | 0.8811 | 0.8840 | +0.0030 |
| Judge 1 | 0.9227 | 0.9244 | +0.0017 |
| Judge 2 | 0.9633 | 0.9664 | +0.0032 |
| Judge 3 | 0.9276 | 0.9293 | +0.0017 |
| Expanded judge set | 0.6648 | 0.7887 | +0.1239 |
| Silver 20K | 0.8745 | 0.9089 | +0.0344 |
| External reviewer | 0.7106 | 0.7828 | +0.0722 |
| Blind technical recruiter | 0.8718 | 0.8746 | +0.0028 |

Mean across the seven internal worlds rises from 0.8727 to 0.8971. The new
ranking overlaps `main` on 70 of 100 candidates. Output SHA-256 from the first
full run: `7D9DD8EFC7483852C0FD9AE1EB4B3894C8F17C945C7FAF31B3764384D40C0A3B`.

## Direct rank-fusion ceiling

`experiments/public_rank_fusion.py` can combine local public CSVs for research.
A conservative fusion (lock the clean top 20, then weighted RRF) raised the
seven-world mean as high as 0.9079 while remaining above `main` on all nine
checks. This is not the branch submission because it directly depends on other
participants' outputs and would not satisfy the clean-room/reproducibility bar.

## Current decision

`top23-clean` is the champion candidate on this branch. The default `main`
profile remains byte-compatible and is not changed unless the opt-in flag is
used. A second full run, complete test suite, Docker run, and byte-hash check
remain required before promotion.
