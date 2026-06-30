# Exhaustive main vs V3 vs V4 vs public field

Generated: 2026-06-29

## Plain-language verdict

V4 is the strongest local version and the most robust internal scorer measured. It beats main on all 15 composite evaluators and improves or ties every one of V3's 60 component cells. It is #1 across the seven internal evaluator mean in the refreshed public field.

It is **not** best on every specialist public axis: 13 public outputs are ahead on H2, 114 coverage-qualified outputs are ahead on the reviewer slice, and 22 are ahead on the blind recruiter slice. Two public outputs also exceed V4 on a simple equal-weight four-axis average. No public output dominates V4 on H2 + mean7 + reviewer + blind simultaneously, so V4 remains on the Pareto frontier. Across all 15 evaluators, V4 is #1 against the 99 revalidated strongest-union artifacts: 0.909790 versus the best public 0.907475.

All numbers are development proxies, not an official hidden score.

## Scope and scoring

Fresh GitHub census: **1,367 discovered**, **1,279 eligible**, **672 valid 100-row outputs**. Each public repository receives its best valid H2 artifact, which is deliberately generous to competitors. The strongest union contains 108 repositories: 99 with a revalidated output and 9 engineering-only leaders without a valid output.

Composite = `0.50 * NDCG@10 + 0.30 * NDCG@50 + 0.15 * MAP + 0.05 * P@10`. Unlabeled candidates are excluded, and coverage is reported. Reviewer ranks require at least 30% coverage; blind ranks require at least 15%.

## Local headline comparison

| Parameter | Main | V3 | V4 |
|---|---:|---:|---:|
| SHA-256 | `24f84f4b6160...` | `c28857fdba63...` | `79aebff697cb...` |
| Mean composite, first 7 | 0.872686 | 0.905883 | 0.906534 |
| Mean composite, all 15 | 0.875238 | 0.909471 | 0.909790 |
| Component cells vs V4 | 35 V4 wins / 23 ties / 2 V4 losses | 9 V4 wins / 51 ties / 0 V4 losses | baseline |
| Composite axes vs V4 | 15 V4 wins / 0 ties / 0 V4 losses | 6 V4 wins / 9 ties / 0 V4 losses | baseline |
| Temporal anomalies | 44 | 59 | 57 |
| Standard flags/disqualifications | 15 | 6 | 6 |
| Honeypots emitted | 0 | 0 | 0 |
| 2 CPU / 16 GB pipeline time | not same-image measured | 91.3 s | 75.4 s |
| 2 CPU / 16 GB wall time | not same-image measured | 95.7 s | 79.5 s |
| Score range | 0.009901 to 0.990099 | 0.278312 to 1.000000 | 0.278312 to 1.000000 |
| Average emitted score | 0.500000 | 0.586628 | 0.586628 |

Score scales are profile-specific; rank order and evaluator metrics are comparable, raw score magnitudes are not.

## All 15 composite scores

| Evaluator | Main | V3 | V4 | V4-Main | V4-V3 |
|---|---:|---:|---:|---:|---:|
| h2 | 0.874834 | 0.881992 | 0.884206 | +0.009372 | +0.002214 |
| independent | 0.881061 | 0.885906 | 0.888246 | +0.007186 | +0.002340 |
| judge1 | 0.922722 | 0.932111 | 0.932111 | +0.009389 | +0.000000 |
| judge2 | 0.963277 | 0.966594 | 0.966594 | +0.003317 | +0.000000 |
| judge3 | 0.927608 | 0.942095 | 0.942095 | +0.014488 | +0.000000 |
| expand | 0.664808 | 0.814569 | 0.814569 | +0.149760 | +0.000000 |
| silver20k | 0.874490 | 0.917915 | 0.917915 | +0.043425 | +0.000000 |
| reviewer | 0.710627 | 0.809603 | 0.809603 | +0.098977 | +0.000000 |
| blind | 0.871825 | 0.896915 | 0.896915 | +0.025090 | +0.000000 |
| merged_j1 | 0.891534 | 0.906120 | 0.906120 | +0.014587 | +0.000000 |
| merged_j2 | 0.959117 | 0.973531 | 0.973531 | +0.014414 | +0.000000 |
| merged_j3 | 0.919047 | 0.942544 | 0.942545 | +0.023498 | +0.000001 |
| relabel_j4 | 0.948109 | 0.963641 | 0.963641 | +0.015532 | +0.000000 |
| relabel_g25 | 0.787073 | 0.839347 | 0.839347 | +0.052274 | +0.000000 |
| blind_test_frozen | 0.932442 | 0.969178 | 0.969412 | +0.036970 | +0.000234 |
| mean7 | 0.872686 | 0.905883 | 0.906534 | +0.033848 | +0.000651 |
| mean15 | 0.875238 | 0.909471 | 0.909790 | +0.034552 | +0.000319 |

## Every NDCG@10 value

| Evaluator | Main | V3 | V4 | V4-Main | V4-V3 |
|---|---:|---:|---:|---:|---:|
| h2 | 0.828822 | 0.824859 | 0.828421 | -0.000401 | +0.003562 |
| independent | 0.876890 | 0.872698 | 0.876466 | -0.000425 | +0.003768 |
| judge1 | 0.894279 | 0.910366 | 0.910366 | +0.016086 | +0.000000 |
| judge2 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| judge3 | 0.943202 | 0.967163 | 0.967163 | +0.023961 | +0.000000 |
| expand | 0.620379 | 0.870382 | 0.870382 | +0.250003 | +0.000000 |
| silver20k | 0.908809 | 0.954897 | 0.954897 | +0.046087 | +0.000000 |
| reviewer | 0.797727 | 0.949103 | 0.949103 | +0.151376 | +0.000000 |
| blind | 0.903842 | 0.918475 | 0.918475 | +0.014632 | +0.000000 |
| merged_j1 | 0.894279 | 0.910366 | 0.910366 | +0.016086 | +0.000000 |
| merged_j2 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| merged_j3 | 0.943202 | 0.967163 | 0.967163 | +0.023961 | +0.000000 |
| relabel_j4 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| relabel_g25 | 0.745203 | 0.821718 | 0.821718 | +0.076515 | +0.000000 |
| blind_test_frozen | 0.919185 | 0.980228 | 0.980606 | +0.061421 | +0.000378 |

## Every NDCG@50 value

| Evaluator | Main | V3 | V4 | V4-Main | V4-V3 |
|---|---:|---:|---:|---:|---:|
| h2 | 0.868077 | 0.898543 | 0.899986 | +0.031909 | +0.001443 |
| independent | 0.814026 | 0.831857 | 0.833377 | +0.019352 | +0.001520 |
| judge1 | 0.925959 | 0.929758 | 0.929758 | +0.003799 | +0.000000 |
| judge2 | 0.877589 | 0.888647 | 0.888647 | +0.011058 | +0.000000 |
| judge3 | 0.868166 | 0.875406 | 0.875406 | +0.007240 | +0.000000 |
| expand | 0.515396 | 0.597926 | 0.597926 | +0.082529 | +0.000000 |
| silver20k | 0.755357 | 0.801555 | 0.801555 | +0.046197 | +0.000000 |
| reviewer | 0.708722 | 0.726943 | 0.726943 | +0.018220 | +0.000000 |
| blind | 0.874679 | 0.918026 | 0.918026 | +0.043347 | +0.000000 |
| merged_j1 | 0.820597 | 0.841833 | 0.841833 | +0.021237 | +0.000000 |
| merged_j2 | 0.863722 | 0.911769 | 0.911769 | +0.048047 | +0.000000 |
| merged_j3 | 0.836790 | 0.874194 | 0.874194 | +0.037404 | +0.000000 |
| relabel_j4 | 0.827030 | 0.878805 | 0.878805 | +0.051775 | +0.000000 |
| relabel_g25 | 0.721075 | 0.767119 | 0.767119 | +0.046044 | +0.000000 |
| blind_test_frozen | 0.909497 | 0.930213 | 0.930362 | +0.020866 | +0.000149 |

## Every MAP value

| Evaluator | Main | V3 | V4 | V4-Main | V4-V3 |
|---|---:|---:|---:|---:|---:|
| h2 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| independent | 0.989384 | 1.000000 | 1.000000 | +0.010616 | +0.000000 |
| judge1 | 0.985297 | 0.986669 | 0.986669 | +0.001372 | +0.000000 |
| judge2 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| judge3 | 0.970378 | 0.972612 | 0.972612 | +0.002234 | +0.000000 |
| expand | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| silver20k | 0.956522 | 1.000000 | 1.000000 | +0.043478 | +0.000000 |
| reviewer | 0.427642 | 0.479792 | 0.479792 | +0.052149 | +0.000000 |
| blind | 0.816667 | 0.848465 | 0.848465 | +0.031798 | +0.000000 |
| merged_j1 | 0.988100 | 0.989249 | 0.989251 | +0.001151 | +0.000002 |
| merged_j2 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| merged_j3 | 0.976060 | 0.978027 | 0.978036 | +0.001976 | +0.000010 |
| relabel_j4 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| relabel_g25 | 0.987660 | 0.989012 | 0.989015 | +0.001355 | +0.000003 |
| blind_test_frozen | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |

## Every P@10 value

| Evaluator | Main | V3 | V4 | V4-Main | V4-V3 |
|---|---:|---:|---:|---:|---:|
| h2 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| independent | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| judge1 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| judge2 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| judge3 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| expand | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| silver20k | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| reviewer | 0.700000 | 0.900000 | 0.900000 | +0.200000 | +0.000000 |
| blind | 0.700000 | 0.700000 | 0.700000 | +0.000000 | +0.000000 |
| merged_j1 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| merged_j2 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| merged_j3 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| relabel_j4 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| relabel_g25 | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |
| blind_test_frozen | 1.000000 | 1.000000 | 1.000000 | +0.000000 | +0.000000 |

## Coverage and label counts

| Evaluator | Labels | Main scored | V3 scored | V4 scored |
|---|---:|---:|---:|---:|
| h2 | 100000 | 100 (100%) | 100 (100%) | 100 (100%) |
| independent | 100000 | 100 (100%) | 100 (100%) | 100 (100%) |
| judge1 | 249 | 69 (69%) | 76 (76%) | 76 (76%) |
| judge2 | 249 | 69 (69%) | 76 (76%) | 76 (76%) |
| judge3 | 249 | 69 (69%) | 76 (76%) | 76 (76%) |
| expand | 639 | 28 (28%) | 24 (24%) | 24 (24%) |
| silver20k | 20000 | 23 (23%) | 25 (25%) | 25 (25%) |
| reviewer | 180 | 57 (57%) | 62 (62%) | 62 (62%) |
| blind | 50 | 19 (19%) | 24 (24%) | 24 (24%) |
| merged_j1 | 281 | 86 (86%) | 94 (94%) | 95 (95%) |
| merged_j2 | 281 | 86 (86%) | 94 (94%) | 95 (95%) |
| merged_j3 | 281 | 86 (86%) | 94 (94%) | 95 (95%) |
| relabel_j4 | 135 | 83 (83%) | 91 (91%) | 92 (92%) |
| relabel_g25 | 136 | 83 (83%) | 92 (92%) | 93 (93%) |
| blind_test_frozen | 1000 | 95 (95%) | 99 (99%) | 99 (99%) |

## Ranking structure

| Pair | Top-10 overlap | Top-100 overlap | Same exact rank |
|---|---:|---:|---:|
| main vs v3 | 8 | 71 | 4 |
| main vs v4 | 8 | 71 | 4 |
| v3 vs v4 | 10 | 98 | 96 |

V4 changes four V3 rows: a feature-based top-band swap and two clean membership backfills.

## Refreshed public-field position

| Axis | Main | V3 | V4 |
|---|---:|---:|---:|
| H2 | #24 / 673 (0.874834) | #16 / 673 (0.881992) | #14 / 673 (0.884206) |
| Seven-evaluator mean | #11 / 673 (0.872686) | #1 / 673 (0.905883) | #1 / 673 (0.906534) |
| Reviewer (at least 30% coverage) | #293 / 430 (0.710627) | #115 / 430 (0.809603) | #115 / 430 (0.809603) |
| Blind recruiter (at least 15% coverage) | #51 / 325 (0.871825) | #23 / 325 (0.896915) | #23 / 325 (0.896915) |
| Equal four-axis mean | #60 / 322 (0.832493) | #3 / 322 (0.873598) | #3 / 322 (0.874314) |
| Mean15 among strongest union | #27 / 100 (0.875238) | #1 / 100 (0.909471) | #1 / 100 (0.909790) |

### Top 25 H2 specialists

| # | Repository | H2 | Mean7 | Reviewer | Blind | Eng. |
|---|---:|---:|---:|---:|---:|---:|
| 1 | [soy-praveen/redrob-ranker](https://github.com/soy-praveen/redrob-ranker) | 0.929965 | 0.889831 | 0.783224 (63%) | 0.879343 (22%) | 10 |
| 2 | [HarshwardhanBhaskar/india-runs-challenge](https://github.com/HarshwardhanBhaskar/india-runs-challenge) | 0.911788 | 0.827557 | 0.589187 (45%) | 0.657735 (18%) | 0 |
| 3 | [Ksmashhero06/redrob-intelligent-candidate-ranker](https://github.com/Ksmashhero06/redrob-intelligent-candidate-ranker) | 0.907746 | 0.750395 | 0.583655 (46%) | 0.563222 (17%) | 6 |
| 4 | [candyflipgit/redrob-candidate-ranker](https://github.com/candyflipgit/redrob-candidate-ranker) | 0.905162 | 0.877395 | 0.733925 (70%) | 0.892000 (25%) | 11 |
| 5 | [ragucreation/india-runs_data_ai](https://github.com/ragucreation/india-runs_data_ai) | 0.897711 | 0.845060 | 0.685967 (53%) | 0.622862 (22%) | 7 |
| 6 | [roug047/India_runs_data_and_ai_challenge](https://github.com/roug047/India_runs_data_and_ai_challenge) | 0.895454 | 0.853349 | 0.820078 (58%) | 0.870225 (20%) | 7 |
| 7 | [Disha-Ambhore/india-runs-intelligent-candidate-ranking](https://github.com/Disha-Ambhore/india-runs-intelligent-candidate-ranking) | 0.893433 | 0.853943 | 0.771132 (57%) | 0.836117 (23%) | 1 |
| 8 | [devanshuk3/Redrob-Codebase](https://github.com/devanshuk3/Redrob-Codebase) | 0.892153 | 0.873460 | 0.774668 (58%) | 0.883458 (24%) | 12 |
| 9 | [Indira-06-Projects/Smart-Candidate-Ranker](https://github.com/Indira-06-Projects/Smart-Candidate-Ranker) | 0.891940 | 0.845192 | 0.653005 (54%) | 0.774601 (21%) | 12 |
| 10 | [thisisgulshanshah/redrob-intelligent-ranking](https://github.com/thisisgulshanshah/redrob-intelligent-ranking) | 0.889726 | 0.822990 | 0.673431 (62%) | 0.769237 (22%) | 14 |
| 11 | [HimanshuRa0/redrob_candidate_ranker](https://github.com/HimanshuRa0/redrob_candidate_ranker) | 0.888139 | 0.846170 | 0.773116 (67%) | 0.830635 (23%) | 5 |
| 12 | [ammu5406/redrob-intel-ranker](https://github.com/ammu5406/redrob-intel-ranker) | 0.888102 | 0.833510 | 0.787559 (48%) | 0.750883 (19%) | 4 |
| 13 | [Praneetb2929/redrob-ranker](https://github.com/Praneetb2929/redrob-ranker) | 0.884222 | 0.810418 | 0.785706 (48%) | 0.810817 (17%) | 1 |
| 14 | [nimishaagarwal20/redrob-semantic-ranker](https://github.com/nimishaagarwal20/redrob-semantic-ranker) | 0.883995 | 0.843389 | 0.789309 (57%) | 0.762959 (19%) | 5 |
| 15 | [Ritesh-Routray/India_Runs_Hackathon](https://github.com/Ritesh-Routray/India_Runs_Hackathon) | 0.882940 | 0.821617 | 0.540156 (54%) | 0.557899 (22%) | 3 |
| 16 | [Ajeets6/IndiaRunsHackathon](https://github.com/Ajeets6/IndiaRunsHackathon) | 0.881693 | 0.868252 | 0.793397 (62%) | 0.873940 (22%) | 6 |
| 17 | [dhakksinesh/redrob-candidate-ranker](https://github.com/dhakksinesh/redrob-candidate-ranker) | 0.878909 | 0.853664 | 0.808052 (66%) | 0.868103 (24%) | 4 |
| 18 | [Harshdeep47/redrob-candidate-ranking](https://github.com/Harshdeep47/redrob-candidate-ranking) | 0.878723 | 0.854863 | 0.801883 (62%) | 0.786938 (20%) | 7 |
| 19 | [Ayushpani/india_runs_hackathon](https://github.com/Ayushpani/india_runs_hackathon) | 0.878233 | 0.831838 | 0.735316 (42%) | 0.756033 (14%) | 11 |
| 20 | [blunterdecosta123/RedrobAI](https://github.com/blunterdecosta123/RedrobAI) | 0.876275 | 0.759841 | 0.663180 (52%) | 0.579469 (18%) | -1 |
| 21 | [ganduripranathi02/redrob-ai-ranker](https://github.com/ganduripranathi02/redrob-ai-ranker) | 0.875472 | 0.864753 | 0.813220 (63%) | 0.784020 (23%) | 1 |
| 22 | [anushkamaisa/HireRank-AI](https://github.com/anushkamaisa/HireRank-AI) | 0.875400 | 0.867965 | 0.832450 (68%) | 0.858072 (24%) | 8 |
| 23 | [thelegendaryarticuno/Devils_den_india_runs_hackathon_](https://github.com/thelegendaryarticuno/Devils_den_india_runs_hackathon_) | 0.874937 | 0.880048 | 0.794562 (67%) | 0.775492 (22%) | 8 |
| 24 | [PIYUSH-BHAVSAR/redrob_ranking](https://github.com/PIYUSH-BHAVSAR/redrob_ranking) | 0.874283 | 0.780907 | 0.497284 (51%) | 0.230216 (16%) | 7 |
| 25 | [kumarvishal01971/INDIA_runs_Data_and_Ai](https://github.com/kumarvishal01971/INDIA_runs_Data_and_Ai) | 0.873090 | 0.836130 | 0.741034 (64%) | 0.852564 (21%) | 2 |

### Top 25 Seven-world mean leaders

| # | Repository | H2 | Mean7 | Reviewer | Blind | Eng. |
|---|---:|---:|---:|---:|---:|---:|
| 1 | [soy-praveen/redrob-ranker](https://github.com/soy-praveen/redrob-ranker) | 0.929965 | 0.889831 | 0.783224 (63%) | 0.879343 (22%) | 10 |
| 2 | [Brammaayya/redrob-hackathon](https://github.com/Brammaayya/redrob-hackathon) | 0.837695 | 0.881414 | 0.874622 (58%) | 0.882691 (18%) | 0 |
| 3 | [thelegendaryarticuno/Devils_den_india_runs_hackathon_](https://github.com/thelegendaryarticuno/Devils_den_india_runs_hackathon_) | 0.874937 | 0.880048 | 0.794562 (67%) | 0.775492 (22%) | 8 |
| 4 | [gatoj273212/redrob-candidate-ranking](https://github.com/gatoj273212/redrob-candidate-ranking) | 0.872909 | 0.879970 | 0.784029 (64%) | 0.893052 (23%) | 4 |
| 5 | [Ashrua7-7/redrob-caliber](https://github.com/Ashrua7-7/redrob-caliber) | 0.865634 | 0.879396 | 0.687561 (63%) | 0.785280 (25%) | 4 |
| 6 | [candyflipgit/redrob-candidate-ranker](https://github.com/candyflipgit/redrob-candidate-ranker) | 0.905162 | 0.877395 | 0.733925 (70%) | 0.892000 (25%) | 11 |
| 7 | [k25kar/redrob-ranker](https://github.com/k25kar/redrob-ranker) | 0.870601 | 0.874129 | 0.847454 (68%) | 0.821951 (24%) | 4 |
| 8 | [devanshuk3/Redrob-Codebase](https://github.com/devanshuk3/Redrob-Codebase) | 0.892153 | 0.873460 | 0.774668 (58%) | 0.883458 (24%) | 12 |
| 9 | [Saran-Priyan/Redrob](https://github.com/Saran-Priyan/Redrob) | 0.863889 | 0.873441 | 0.777932 (69%) | 0.776334 (23%) | 4 |
| 10 | [AbhayBhise/REDROB-AI-](https://github.com/AbhayBhise/REDROB-AI-) | 0.861271 | 0.872920 | 0.744839 (69%) | 0.812243 (24%) | 8 |
| 11 | [sravanyadav-19/redrob-intelligent-candidate-ranking](https://github.com/sravanyadav-19/redrob-intelligent-candidate-ranking) | 0.860679 | 0.871594 | 0.764619 (70%) | 0.818547 (24%) | 11 |
| 12 | [atharvdate/redrob-india-runs-ai-ranking](https://github.com/atharvdate/redrob-india-runs-ai-ranking) | 0.794016 | 0.870049 | 0.836418 (75%) | 0.876836 (27%) | 8 |
| 13 | [Harivelu0/redrob-ranker](https://github.com/Harivelu0/redrob-ranker) | 0.871836 | 0.869636 | 0.708755 (62%) | 0.840078 (23%) | 11 |
| 14 | [garg-khushi/redrob-talentrank-os](https://github.com/garg-khushi/redrob-talentrank-os) | 0.856855 | 0.869589 | 0.789398 (70%) | 0.787154 (27%) | 3 |
| 15 | [Ajeets6/IndiaRunsHackathon](https://github.com/Ajeets6/IndiaRunsHackathon) | 0.881693 | 0.868252 | 0.793397 (62%) | 0.873940 (22%) | 6 |
| 16 | [anushkamaisa/HireRank-AI](https://github.com/anushkamaisa/HireRank-AI) | 0.875400 | 0.867965 | 0.832450 (68%) | 0.858072 (24%) | 8 |
| 17 | [Charnjot333/Redrob-Ranker](https://github.com/Charnjot333/Redrob-Ranker) | 0.837100 | 0.867332 | 0.693427 (64%) | 0.878757 (22%) | 2 |
| 18 | [Roalphi/redrobai_hackathon](https://github.com/Roalphi/redrobai_hackathon) | 0.869865 | 0.865618 | 0.824803 (60%) | 0.950850 (21%) | 3 |
| 19 | [Kirtiraj666/redrob_ranker](https://github.com/Kirtiraj666/redrob_ranker) | 0.871055 | 0.865235 | 0.760098 (78%) | 0.849800 (26%) | 5 |
| 20 | [ganduripranathi02/redrob-ai-ranker](https://github.com/ganduripranathi02/redrob-ai-ranker) | 0.875472 | 0.864753 | 0.813220 (63%) | 0.784020 (23%) | 1 |
| 21 | [tanishq7389/redrob-ranker](https://github.com/tanishq7389/redrob-ranker) | 0.863907 | 0.863639 | 0.769840 (56%) | 0.831049 (23%) | 1 |
| 22 | [Ayush-Kumar0207/Redrob](https://github.com/Ayush-Kumar0207/Redrob) | 0.864670 | 0.863316 | 0.849247 (63%) | 0.945907 (22%) | 16 |
| 23 | [sanyamm27/redrob-ranker](https://github.com/sanyamm27/redrob-ranker) | 0.855730 | 0.860392 | 0.835881 (66%) | 0.842491 (27%) | -2 |
| 24 | [AnkanDasBarman/redrob-ranker](https://github.com/AnkanDasBarman/redrob-ranker) | 0.761986 | 0.859182 | 0.830658 (60%) | 0.802867 (21%) | 6 |
| 25 | [khushii1412/redrob-candidate-ranking](https://github.com/khushii1412/redrob-candidate-ranking) | 0.860513 | 0.858757 | 0.821300 (66%) | 0.862277 (21%) | 5 |

### Top 25 Reviewer specialists

| # | Repository | H2 | Mean7 | Reviewer | Blind | Eng. |
|---|---:|---:|---:|---:|---:|---:|
| 1 | [SANKALP9TRIPATHI/Redrob](https://github.com/SANKALP9TRIPATHI/Redrob) | 0.729974 | 0.753899 | 0.934955 (40%) | 0.891392 (12%) | 9 |
| 2 | [vipansh93/India_Runs](https://github.com/vipansh93/India_Runs) | 0.768128 | 0.787977 | 0.910693 (47%) | 0.869029 (14%) | 0 |
| 3 | [vipansh93/India_Runs2](https://github.com/vipansh93/India_Runs2) | 0.768128 | 0.787977 | 0.910693 (47%) | 0.869029 (14%) | 4 |
| 4 | [Mohammadsiraj07/Redrob_Hackathon](https://github.com/Mohammadsiraj07/Redrob_Hackathon) | 0.784495 | 0.760634 | 0.910498 (43%) | 0.942152 (13%) | 11 |
| 5 | [milindnair/INDIA-RUNS](https://github.com/milindnair/INDIA-RUNS) | 0.808852 | 0.833760 | 0.904842 (55%) | 0.832228 (14%) | 7 |
| 6 | [shikhar1809/Sifter_Redrob_Hackathon](https://github.com/shikhar1809/Sifter_Redrob_Hackathon) | 0.796774 | 0.809539 | 0.903919 (63%) | 0.909096 (23%) | 12 |
| 7 | [Muheet-Mehraj/redrob-matching-engine](https://github.com/Muheet-Mehraj/redrob-matching-engine) | 0.808724 | 0.809515 | 0.902902 (48%) | 0.966756 (20%) | 6 |
| 8 | [bhupesho45/redrob-ai-candidate-ranking](https://github.com/bhupesho45/redrob-ai-candidate-ranking) | 0.790277 | 0.779966 | 0.897295 (61%) | 0.872259 (21%) | 2 |
| 9 | [dharanh72-cloud/redrob-ranker](https://github.com/dharanh72-cloud/redrob-ranker) | 0.790654 | 0.792478 | 0.896583 (45%) | 0.882456 (15%) | 12 |
| 10 | [Jothik1506-ai/India-Runs-Hackathon_Team-Dev-DUO](https://github.com/Jothik1506-ai/India-Runs-Hackathon_Team-Dev-DUO) | 0.814121 | 0.809637 | 0.893592 (55%) | 0.743439 (19%) | 10 |
| 11 | [raviprakash720/India-runs](https://github.com/raviprakash720/India-runs) | 0.798377 | 0.787744 | 0.889667 (40%) | 0.945251 (14%) | 5 |
| 12 | [rishicodesforfun/India-runs-ats](https://github.com/rishicodesforfun/India-runs-ats) | 0.779368 | 0.776216 | 0.888400 (40%) | 0.913355 (13%) | 9 |
| 13 | [Varshini-R1181/redrob-ranker](https://github.com/Varshini-R1181/redrob-ranker) | 0.771551 | 0.782095 | 0.886247 (44%) | 0.952480 (15%) | 2 |
| 14 | [GritHri/Redrob_Hackathon_Solution](https://github.com/GritHri/Redrob_Hackathon_Solution) | 0.767082 | 0.807499 | 0.885915 (54%) | 0.832828 (16%) | 8 |
| 15 | [ranejai954/india-runs-track1-submission](https://github.com/ranejai954/india-runs-track1-submission) | 0.726022 | 0.762835 | 0.885117 (57%) | 0.875357 (19%) | 2 |
| 16 | [vanampranav/RedRob](https://github.com/vanampranav/RedRob) | 0.829803 | 0.817622 | 0.884638 (69%) | 0.755557 (23%) | 6 |
| 17 | [Jatin0Jain/IndiaRunsSubmission-Candidate-Ranker](https://github.com/Jatin0Jain/IndiaRunsSubmission-Candidate-Ranker) | 0.802652 | 0.768560 | 0.883303 (41%) | 0.843439 (14%) | 5 |
| 18 | [vishaal-patil/AI_Hackathon_India_Runs](https://github.com/vishaal-patil/AI_Hackathon_India_Runs) | 0.814944 | 0.748785 | 0.880668 (42%) | 0.888323 (17%) | 4 |
| 19 | [dakshDogra07/redrob-ranker](https://github.com/dakshDogra07/redrob-ranker) | 0.751839 | 0.721037 | 0.878986 (41%) | 0.862110 (12%) | 10 |
| 20 | [0xSHSH/redrob-talentgraph-ai](https://github.com/0xSHSH/redrob-talentgraph-ai) | 0.836610 | 0.833529 | 0.877739 (64%) | 0.907832 (23%) | 15 |
| 21 | [krishna-yesaswini/redrob-ranker](https://github.com/krishna-yesaswini/redrob-ranker) | 0.739747 | 0.773109 | 0.877091 (55%) | 0.867468 (19%) | 1 |
| 22 | [Brammaayya/redrob-hackathon](https://github.com/Brammaayya/redrob-hackathon) | 0.837695 | 0.881414 | 0.874622 (58%) | 0.882691 (18%) | 0 |
| 23 | [Palak24Ol/IndiaRuns_DataAndAIChallenge](https://github.com/Palak24Ol/IndiaRuns_DataAndAIChallenge) | 0.771238 | 0.837319 | 0.874605 (72%) | 0.884657 (22%) | 7 |
| 24 | [HanshikaSahu/RedRob-TalentMatchAI](https://github.com/HanshikaSahu/RedRob-TalentMatchAI) | 0.838040 | 0.807918 | 0.873369 (49%) | 0.966756 (20%) | 4 |
| 25 | [PurviGit/redrob-ranker](https://github.com/PurviGit/redrob-ranker) | 0.842987 | 0.853926 | 0.872646 (60%) | 0.801234 (25%) | 7 |

### Top 25 Blind-recruiter specialists

| # | Repository | H2 | Mean7 | Reviewer | Blind | Eng. |
|---|---:|---:|---:|---:|---:|---:|
| 1 | [HanshikaSahu/RedRob-TalentMatchAI](https://github.com/HanshikaSahu/RedRob-TalentMatchAI) | 0.838040 | 0.807918 | 0.873369 (49%) | 0.966756 (20%) | 4 |
| 2 | [Muheet-Mehraj/redrob-matching-engine](https://github.com/Muheet-Mehraj/redrob-matching-engine) | 0.808724 | 0.809515 | 0.902902 (48%) | 0.966756 (20%) | 6 |
| 3 | [divyamamidala2406/redrob-ranker](https://github.com/divyamamidala2406/redrob-ranker) | 0.813680 | 0.849779 | 0.853663 (63%) | 0.964452 (23%) | 4 |
| 4 | [Varshini-R1181/redrob-ranker](https://github.com/Varshini-R1181/redrob-ranker) | 0.771551 | 0.782095 | 0.886247 (44%) | 0.952480 (15%) | 2 |
| 5 | [Shristi1611/redrob-intelligent-ranker](https://github.com/Shristi1611/redrob-intelligent-ranker) | 0.847230 | 0.823433 | 0.846544 (61%) | 0.951557 (21%) | 8 |
| 6 | [Roalphi/redrobai_hackathon](https://github.com/Roalphi/redrobai_hackathon) | 0.869865 | 0.865618 | 0.824803 (60%) | 0.950850 (21%) | 3 |
| 7 | [Ayush-Kumar0207/Redrob](https://github.com/Ayush-Kumar0207/Redrob) | 0.864670 | 0.863316 | 0.849247 (63%) | 0.945907 (22%) | 16 |
| 8 | [NAMPALLY-PRANAY/redrob_h2s_hackathon](https://github.com/NAMPALLY-PRANAY/redrob_h2s_hackathon) | 0.841852 | 0.827267 | 0.780584 (69%) | 0.941581 (24%) | 4 |
| 9 | [Chiranjeevibathula/redrob-ai-candidate-ranking](https://github.com/Chiranjeevibathula/redrob-ai-candidate-ranking) | 0.819171 | 0.802418 | 0.862181 (54%) | 0.938370 (23%) | 4 |
| 10 | [Preethamkumarkothakonda/redrob_ai_smart_recruiter](https://github.com/Preethamkumarkothakonda/redrob_ai_smart_recruiter) | 0.864941 | 0.841229 | 0.803841 (64%) | 0.931914 (23%) | 9 |
| 11 | [madhav1431-create/redrob-candidate-ranker](https://github.com/madhav1431-create/redrob-candidate-ranker) | 0.824981 | 0.828986 | 0.851524 (67%) | 0.928758 (27%) | 4 |
| 12 | [spg3098-alt/redrob-ranker](https://github.com/spg3098-alt/redrob-ranker) | 0.793731 | 0.826253 | 0.830416 (54%) | 0.920631 (16%) | 5 |
| 13 | [joyjit-das/redrob-ranker](https://github.com/joyjit-das/redrob-ranker) | 0.841142 | 0.848424 | 0.865144 (56%) | 0.917958 (20%) | 6 |
| 14 | [supreethi2730/Redrob-Candidate-Ranker](https://github.com/supreethi2730/Redrob-Candidate-Ranker) | 0.719343 | 0.786193 | 0.766647 (70%) | 0.913512 (27%) | 2 |
| 15 | [Jigar8800/redrob-ai-candidate-ranker](https://github.com/Jigar8800/redrob-ai-candidate-ranker) | 0.858771 | 0.821887 | 0.798815 (46%) | 0.912584 (17%) | 3 |
| 16 | [Kartik-37/India_runs_data_and_ai_challenge](https://github.com/Kartik-37/India_runs_data_and_ai_challenge) | 0.858771 | 0.821887 | 0.798815 (46%) | 0.912584 (17%) | 3 |
| 17 | [Drishti84/-redrob_ranker](https://github.com/Drishti84/-redrob_ranker) | 0.775921 | 0.773597 | 0.841769 (60%) | 0.911176 (23%) | 4 |
| 18 | [shikhar1809/Sifter_Redrob_Hackathon](https://github.com/shikhar1809/Sifter_Redrob_Hackathon) | 0.796774 | 0.809539 | 0.903919 (63%) | 0.909096 (23%) | 12 |
| 19 | [0xSHSH/redrob-talentgraph-ai](https://github.com/0xSHSH/redrob-talentgraph-ai) | 0.836610 | 0.833529 | 0.877739 (64%) | 0.907832 (23%) | 15 |
| 20 | [aaryanpawar16/Redrob-AI-Candidate-Ranker](https://github.com/aaryanpawar16/Redrob-AI-Candidate-Ranker) | 0.827570 | 0.854374 | 0.861455 (64%) | 0.905086 (22%) | 7 |
| 21 | [hemasaini011/redrob-ranker](https://github.com/hemasaini011/redrob-ranker) | 0.793836 | 0.835198 | 0.857966 (60%) | 0.904350 (20%) | 2 |
| 22 | [SandeepKumarDubey7/redrob-ranker](https://github.com/SandeepKumarDubey7/redrob-ranker) | 0.865790 | 0.854294 | 0.825599 (47%) | 0.903383 (18%) | 7 |
| 23 | [poovarasu638178-rgb/redrob-candidate-ranker](https://github.com/poovarasu638178-rgb/redrob-candidate-ranker) | 0.782564 | 0.820251 | 0.842859 (58%) | 0.896520 (21%) | 0 |
| 24 | [Vasi1951/redrob-ranking](https://github.com/Vasi1951/redrob-ranking) | 0.837546 | 0.716614 | 0.838998 (39%) | 0.895719 (15%) | 4 |
| 25 | [harshisingh777/Redrob_CodePhattGya](https://github.com/harshisingh777/Redrob_CodePhattGya) | 0.862320 | 0.844628 | 0.820060 (60%) | 0.894364 (25%) | 8 |

## Top 25 equal-weight four-axis balance

| # | Repository | Mean4 | H2 | Mean7 | Reviewer | Blind |
|---|---:|---:|---:|---:|---:|---:|
| 1 | [Ayush-Kumar0207/Redrob](https://github.com/Ayush-Kumar0207/Redrob) | 0.880785 | 0.864670 | 0.863316 | 0.849247 | 0.945907 |
| 2 | [Roalphi/redrobai_hackathon](https://github.com/Roalphi/redrobai_hackathon) | 0.877784 | 0.869865 | 0.865618 | 0.824803 | 0.950850 |
| 3 | `LOCAL/dominant-v4` | 0.874314 | 0.884206 | 0.906534 | 0.809603 | 0.896915 |
| 4 | [Muheet-Mehraj/redrob-matching-engine](https://github.com/Muheet-Mehraj/redrob-matching-engine) | 0.871975 | 0.808724 | 0.809515 | 0.902902 | 0.966756 |
| 5 | [HanshikaSahu/RedRob-TalentMatchAI](https://github.com/HanshikaSahu/RedRob-TalentMatchAI) | 0.871521 | 0.838040 | 0.807918 | 0.873369 | 0.966756 |
| 6 | [soy-praveen/redrob-ranker](https://github.com/soy-praveen/redrob-ranker) | 0.870591 | 0.929965 | 0.889831 | 0.783224 | 0.879343 |
| 7 | [divyamamidala2406/redrob-ranker](https://github.com/divyamamidala2406/redrob-ranker) | 0.870393 | 0.813680 | 0.849779 | 0.853663 | 0.964452 |
| 8 | [Brammaayya/redrob-hackathon](https://github.com/Brammaayya/redrob-hackathon) | 0.869105 | 0.837695 | 0.881414 | 0.874622 | 0.882691 |
| 9 | [joyjit-das/redrob-ranker](https://github.com/joyjit-das/redrob-ranker) | 0.868167 | 0.841142 | 0.848424 | 0.865144 | 0.917958 |
| 10 | [Shristi1611/redrob-intelligent-ranker](https://github.com/Shristi1611/redrob-intelligent-ranker) | 0.867191 | 0.847230 | 0.823433 | 0.846544 | 0.951557 |
| 11 | [0xSHSH/redrob-talentgraph-ai](https://github.com/0xSHSH/redrob-talentgraph-ai) | 0.863928 | 0.836610 | 0.833529 | 0.877739 | 0.907832 |
| 12 | [SandeepKumarDubey7/redrob-ranker](https://github.com/SandeepKumarDubey7/redrob-ranker) | 0.862266 | 0.865790 | 0.854294 | 0.825599 | 0.903383 |
| 13 | [aaryanpawar16/Redrob-AI-Candidate-Ranker](https://github.com/aaryanpawar16/Redrob-AI-Candidate-Ranker) | 0.862121 | 0.827570 | 0.854374 | 0.861455 | 0.905086 |
| 14 | [Preethamkumarkothakonda/redrob_ai_smart_recruiter](https://github.com/Preethamkumarkothakonda/redrob_ai_smart_recruiter) | 0.860481 | 0.864941 | 0.841229 | 0.803841 | 0.931914 |
| 15 | [roug047/India_runs_data_and_ai_challenge](https://github.com/roug047/India_runs_data_and_ai_challenge) | 0.859777 | 0.895454 | 0.853349 | 0.820078 | 0.870225 |
| 16 | [YashhCanCode/RedRob-Ranker](https://github.com/YashhCanCode/RedRob-Ranker) | 0.859201 | 0.856780 | 0.855021 | 0.839583 | 0.885419 |
| 17 | [madhav1431-create/redrob-candidate-ranker](https://github.com/madhav1431-create/redrob-candidate-ranker) | 0.858562 | 0.824981 | 0.828986 | 0.851524 | 0.928758 |
| 18 | [anushkamaisa/HireRank-AI](https://github.com/anushkamaisa/HireRank-AI) | 0.858472 | 0.875400 | 0.867965 | 0.832450 | 0.858072 |
| 19 | [505kjj/Candidate-Intelligence-Dashboard](https://github.com/505kjj/Candidate-Intelligence-Dashboard) | 0.857893 | 0.862397 | 0.833761 | 0.871645 | 0.863769 |
| 20 | [gatoj273212/redrob-candidate-ranking](https://github.com/gatoj273212/redrob-candidate-ranking) | 0.857490 | 0.872909 | 0.879970 | 0.784029 | 0.893052 |
| 21 | [devanshuk3/Redrob-Codebase](https://github.com/devanshuk3/Redrob-Codebase) | 0.855935 | 0.892153 | 0.873460 | 0.774668 | 0.883458 |
| 22 | [Chiranjeevibathula/redrob-ai-candidate-ranking](https://github.com/Chiranjeevibathula/redrob-ai-candidate-ranking) | 0.855535 | 0.819171 | 0.802418 | 0.862181 | 0.938370 |
| 23 | [harshisingh777/Redrob_CodePhattGya](https://github.com/harshisingh777/Redrob_CodePhattGya) | 0.855343 | 0.862320 | 0.844628 | 0.820060 | 0.894364 |
| 24 | [shikhar1809/Sifter_Redrob_Hackathon](https://github.com/shikhar1809/Sifter_Redrob_Hackathon) | 0.854832 | 0.796774 | 0.809539 | 0.903919 | 0.909096 |
| 25 | [Ajeets6/IndiaRunsHackathon](https://github.com/Ajeets6/IndiaRunsHackathon) | 0.854320 | 0.881693 | 0.868252 | 0.793397 | 0.873940 |

This simple mean is descriptive, not the challenge metric; reviewer/blind coverage is much smaller than the internal labels.

## Four-axis Pareto frontier

| Repository | H2 | Mean7 | Reviewer | Blind | Mean4 |
|---|---:|---:|---:|---:|---:|
| [Ayush-Kumar0207/Redrob](https://github.com/Ayush-Kumar0207/Redrob) | 0.864670 | 0.863316 | 0.849247 | 0.945907 | 0.880785 |
| [Roalphi/redrobai_hackathon](https://github.com/Roalphi/redrobai_hackathon) | 0.869865 | 0.865618 | 0.824803 | 0.950850 | 0.877784 |
| `LOCAL/dominant-v4` | 0.884206 | 0.906534 | 0.809603 | 0.896915 | 0.874314 |
| [Muheet-Mehraj/redrob-matching-engine](https://github.com/Muheet-Mehraj/redrob-matching-engine) | 0.808724 | 0.809515 | 0.902902 | 0.966756 | 0.871975 |
| [HanshikaSahu/RedRob-TalentMatchAI](https://github.com/HanshikaSahu/RedRob-TalentMatchAI) | 0.838040 | 0.807918 | 0.873369 | 0.966756 | 0.871521 |
| [soy-praveen/redrob-ranker](https://github.com/soy-praveen/redrob-ranker) | 0.929965 | 0.889831 | 0.783224 | 0.879343 | 0.870591 |
| [divyamamidala2406/redrob-ranker](https://github.com/divyamamidala2406/redrob-ranker) | 0.813680 | 0.849779 | 0.853663 | 0.964452 | 0.870393 |
| [Brammaayya/redrob-hackathon](https://github.com/Brammaayya/redrob-hackathon) | 0.837695 | 0.881414 | 0.874622 | 0.882691 | 0.869105 |
| [joyjit-das/redrob-ranker](https://github.com/joyjit-das/redrob-ranker) | 0.841142 | 0.848424 | 0.865144 | 0.917958 | 0.868167 |
| [Shristi1611/redrob-intelligent-ranker](https://github.com/Shristi1611/redrob-intelligent-ranker) | 0.847230 | 0.823433 | 0.846544 | 0.951557 | 0.867191 |
| [0xSHSH/redrob-talentgraph-ai](https://github.com/0xSHSH/redrob-talentgraph-ai) | 0.836610 | 0.833529 | 0.877739 | 0.907832 | 0.863928 |
| [SandeepKumarDubey7/redrob-ranker](https://github.com/SandeepKumarDubey7/redrob-ranker) | 0.865790 | 0.854294 | 0.825599 | 0.903383 | 0.862266 |
| [aaryanpawar16/Redrob-AI-Candidate-Ranker](https://github.com/aaryanpawar16/Redrob-AI-Candidate-Ranker) | 0.827570 | 0.854374 | 0.861455 | 0.905086 | 0.862121 |
| [roug047/India_runs_data_and_ai_challenge](https://github.com/roug047/India_runs_data_and_ai_challenge) | 0.895454 | 0.853349 | 0.820078 | 0.870225 | 0.859777 |
| [madhav1431-create/redrob-candidate-ranker](https://github.com/madhav1431-create/redrob-candidate-ranker) | 0.824981 | 0.828986 | 0.851524 | 0.928758 | 0.858562 |
| [anushkamaisa/HireRank-AI](https://github.com/anushkamaisa/HireRank-AI) | 0.875400 | 0.867965 | 0.832450 | 0.858072 | 0.858472 |
| [505kjj/Candidate-Intelligence-Dashboard](https://github.com/505kjj/Candidate-Intelligence-Dashboard) | 0.862397 | 0.833761 | 0.871645 | 0.863769 | 0.857893 |
| [devanshuk3/Redrob-Codebase](https://github.com/devanshuk3/Redrob-Codebase) | 0.892153 | 0.873460 | 0.774668 | 0.883458 | 0.855935 |
| [shikhar1809/Sifter_Redrob_Hackathon](https://github.com/shikhar1809/Sifter_Redrob_Hackathon) | 0.796774 | 0.809539 | 0.903919 | 0.909096 | 0.854832 |
| [k25kar/redrob-ranker](https://github.com/k25kar/redrob-ranker) | 0.870601 | 0.874129 | 0.847454 | 0.821951 | 0.853534 |
| [Aki7-web/redrob-ai](https://github.com/Aki7-web/redrob-ai) | 0.872205 | 0.825475 | 0.822516 | 0.889163 | 0.852340 |
| [candyflipgit/redrob-candidate-ranker](https://github.com/candyflipgit/redrob-candidate-ranker) | 0.905162 | 0.877395 | 0.733925 | 0.892000 | 0.852120 |
| [PurviGit/redrob-ranker](https://github.com/PurviGit/redrob-ranker) | 0.842987 | 0.853926 | 0.872646 | 0.801234 | 0.842698 |
| [Palak24Ol/IndiaRuns_DataAndAIChallenge](https://github.com/Palak24Ol/IndiaRuns_DataAndAIChallenge) | 0.771238 | 0.837319 | 0.874605 | 0.884657 | 0.841955 |
| [ganduripranathi02/redrob-ai-ranker](https://github.com/ganduripranathi02/redrob-ai-ranker) | 0.875472 | 0.864753 | 0.813220 | 0.784020 | 0.834366 |
| [vishaal-patil/AI_Hackathon_India_Runs](https://github.com/vishaal-patil/AI_Hackathon_India_Runs) | 0.814944 | 0.748785 | 0.880668 | 0.888323 | 0.833180 |
| [vanampranav/RedRob](https://github.com/vanampranav/RedRob) | 0.829803 | 0.817622 | 0.884638 | 0.755557 | 0.821905 |
| [Jothik1506-ai/India-Runs-Hackathon_Team-Dev-DUO](https://github.com/Jothik1506-ai/India-Runs-Hackathon_Team-Dev-DUO) | 0.814121 | 0.809637 | 0.893592 | 0.743439 | 0.815197 |

A Pareto-front entry cannot be improved on one of these four axes without giving up another. V4 is on this frontier; no public output is at least as good on all four and better on one.

## All strongest-union repositories - every composite parameter

The 99 valid artifacts below were freshly downloaded and matched the census H2 score exactly. Full component metrics are in [`full_comparison_matrix_2026-06-29.csv`](../experiments/full_comparison_matrix_2026-06-29.csv).

| Repository | Selected for | H2 | Ind | J1 | J2 | J3 | Expand | Silver | Reviewer | Blind | MJ1 | MJ2 | MJ3 | J4 | G25 | Frozen | Mean15 | Eng. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| [Brammaayya/redrob-hackathon](https://github.com/Brammaayya/redrob-hackathon) | mean7,reviewer | 0.837695 | 0.830869 | 0.936908 | 0.955767 | 0.962687 | 0.804304 | 0.841669 | 0.874622 | 0.882691 | 0.940929 | 0.961776 | 0.968542 | 0.954227 | 0.889616 | 0.969819 | 0.907475 | 0 |
| [atharvdate/redrob-india-runs-ai-ranking](https://github.com/atharvdate/redrob-india-runs-ai-ranking) | mean7 | 0.794016 | 0.787664 | 0.917319 | 0.966327 | 0.945831 | 0.828556 | 0.850629 | 0.836418 | 0.876836 | 0.904155 | 0.962442 | 0.938571 | 0.948594 | 0.833874 | 0.958672 | 0.889994 | 8 |
| [gatoj273212/redrob-candidate-ranking](https://github.com/gatoj273212/redrob-candidate-ranking) | mean7 | 0.872909 | 0.874615 | 0.845137 | 0.964688 | 0.947098 | 0.782624 | 0.872720 | 0.784029 | 0.893052 | 0.829807 | 0.969893 | 0.946828 | 0.959818 | 0.828755 | 0.957774 | 0.888650 | 4 |
| [soy-praveen/redrob-ranker](https://github.com/soy-praveen/redrob-ranker) | h2,mean7 | 0.929965 | 0.928549 | 0.866192 | 0.956724 | 0.929794 | 0.791857 | 0.825733 | 0.783224 | 0.879343 | 0.849226 | 0.952642 | 0.924970 | 0.944099 | 0.890658 | 0.873363 | 0.888423 | 10 |
| [divyamamidala2406/redrob-ranker](https://github.com/divyamamidala2406/redrob-ranker) | blind | 0.813680 | 0.791620 | 0.883737 | 0.964615 | 0.930693 | 0.689667 | 0.874440 | 0.853663 | 0.964452 | 0.875700 | 0.966298 | 0.934211 | 0.945959 | 0.865546 | 0.955945 | 0.887348 | 4 |
| [k25kar/redrob-ranker](https://github.com/k25kar/redrob-ranker) | mean7 | 0.870601 | 0.857143 | 0.871956 | 0.964285 | 0.937713 | 0.756879 | 0.860327 | 0.847454 | 0.821951 | 0.866322 | 0.962394 | 0.928902 | 0.952207 | 0.835846 | 0.953590 | 0.885838 | 4 |
| [aaryanpawar16/Redrob-AI-Candidate-Ranker](https://github.com/aaryanpawar16/Redrob-AI-Candidate-Ranker) | blind | 0.827570 | 0.836177 | 0.875493 | 0.966406 | 0.937423 | 0.767824 | 0.769724 | 0.861455 | 0.905086 | 0.850314 | 0.972447 | 0.939982 | 0.960600 | 0.840745 | 0.956180 | 0.884495 | 7 |
| [anushkamaisa/HireRank-AI](https://github.com/anushkamaisa/HireRank-AI) | h2,mean7 | 0.875400 | 0.858419 | 0.877170 | 0.943579 | 0.941115 | 0.784113 | 0.795961 | 0.832450 | 0.858072 | 0.870943 | 0.949643 | 0.955122 | 0.942338 | 0.812928 | 0.969246 | 0.884433 | 8 |
| [Ayush-Kumar0207/Redrob](https://github.com/Ayush-Kumar0207/Redrob) | mean7,blind,engineering | 0.864670 | 0.867025 | 0.889115 | 0.957795 | 0.932151 | 0.671538 | 0.860918 | 0.849247 | 0.945907 | 0.886388 | 0.963461 | 0.930596 | 0.940509 | 0.736074 | 0.961625 | 0.883801 | 16 |
| [AbhayBhise/REDROB-AI-](https://github.com/AbhayBhise/REDROB-AI-) | mean7 | 0.861271 | 0.811314 | 0.898973 | 0.964457 | 0.948893 | 0.819776 | 0.805758 | 0.744839 | 0.812243 | 0.916957 | 0.959329 | 0.962215 | 0.950518 | 0.858693 | 0.939508 | 0.883650 | 8 |
| [AnkanDasBarman/redrob-ranker](https://github.com/AnkanDasBarman/redrob-ranker) | mean7 | 0.761986 | 0.766373 | 0.924137 | 0.969151 | 0.968993 | 0.798736 | 0.824895 | 0.830658 | 0.802867 | 0.900940 | 0.976406 | 0.969589 | 0.965787 | 0.841404 | 0.950803 | 0.883515 | 6 |
| [thelegendaryarticuno/Devils_den_india_runs_hackathon_](https://github.com/thelegendaryarticuno/Devils_den_india_runs_hackathon_) | h2,mean7 | 0.874937 | 0.884115 | 0.955359 | 0.955243 | 0.931300 | 0.760920 | 0.798464 | 0.794562 | 0.775492 | 0.936581 | 0.966559 | 0.932539 | 0.922669 | 0.828688 | 0.932232 | 0.883311 | 8 |
| [milindnair/INDIA-RUNS](https://github.com/milindnair/INDIA-RUNS) | reviewer | 0.808852 | 0.791892 | 0.882825 | 0.958886 | 0.950381 | 0.713144 | 0.730339 | 0.904842 | 0.832228 | 0.915792 | 0.958122 | 0.947375 | 0.947247 | 0.953543 | 0.940244 | 0.882381 | 7 |
| [sravanyadav-19/redrob-intelligent-candidate-ranking](https://github.com/sravanyadav-19/redrob-intelligent-candidate-ranking) | mean7 | 0.860679 | 0.814150 | 0.893341 | 0.964814 | 0.936686 | 0.809268 | 0.822220 | 0.764619 | 0.818547 | 0.869366 | 0.965538 | 0.934054 | 0.950503 | 0.868510 | 0.960169 | 0.882164 | 11 |
| [Roalphi/redrobai_hackathon](https://github.com/Roalphi/redrobai_hackathon) | mean7,blind | 0.869865 | 0.880663 | 0.842004 | 0.955925 | 0.935878 | 0.740925 | 0.834067 | 0.824803 | 0.950850 | 0.824238 | 0.958641 | 0.936795 | 0.956723 | 0.776565 | 0.941031 | 0.881932 | 3 |
| [Ajeets6/IndiaRunsHackathon](https://github.com/Ajeets6/IndiaRunsHackathon) | h2,mean7 | 0.881693 | 0.891769 | 0.887383 | 0.967462 | 0.937019 | 0.753233 | 0.759209 | 0.793397 | 0.873940 | 0.864575 | 0.974135 | 0.934891 | 0.969815 | 0.797491 | 0.942461 | 0.881898 | 6 |
| [Charnjot333/Redrob-Ranker](https://github.com/Charnjot333/Redrob-Ranker) | mean7 | 0.837100 | 0.760264 | 0.875704 | 0.969068 | 0.944382 | 0.879795 | 0.805013 | 0.693427 | 0.878757 | 0.846831 | 0.974795 | 0.947465 | 0.970548 | 0.923778 | 0.917575 | 0.881633 | 2 |
| [sanyamm27/redrob-ranker](https://github.com/sanyamm27/redrob-ranker) | mean7 | 0.855730 | 0.840997 | 0.863854 | 0.953717 | 0.953965 | 0.768557 | 0.785928 | 0.835881 | 0.842491 | 0.868284 | 0.963768 | 0.959257 | 0.929516 | 0.873273 | 0.929274 | 0.881633 | -2 |
| [SandeepKumarDubey7/redrob-ranker](https://github.com/SandeepKumarDubey7/redrob-ranker) | blind | 0.865790 | 0.874266 | 0.901602 | 0.955649 | 0.916342 | 0.678476 | 0.787931 | 0.825599 | 0.903383 | 0.889495 | 0.959019 | 0.914738 | 0.940513 | 0.846892 | 0.941053 | 0.880050 | 7 |
| [Harivelu0/redrob-ranker](https://github.com/Harivelu0/redrob-ranker) | mean7 | 0.871836 | 0.777969 | 0.851508 | 0.962484 | 0.959952 | 0.791577 | 0.872128 | 0.708755 | 0.840078 | 0.818080 | 0.961343 | 0.959441 | 0.950130 | 0.889001 | 0.969151 | 0.878895 | 11 |
| [Saran-Priyan/Redrob](https://github.com/Saran-Priyan/Redrob) | mean7 | 0.863889 | 0.867199 | 0.917196 | 0.963078 | 0.942690 | 0.748088 | 0.811948 | 0.777932 | 0.776334 | 0.908958 | 0.972386 | 0.937918 | 0.948517 | 0.788199 | 0.948955 | 0.878219 | 4 |
| [tanishq7389/redrob-ranker](https://github.com/tanishq7389/redrob-ranker) | mean7 | 0.863907 | 0.819982 | 0.858032 | 0.951098 | 0.927353 | 0.765651 | 0.859449 | 0.769840 | 0.831049 | 0.835630 | 0.964398 | 0.939825 | 0.944145 | 0.851016 | 0.985105 | 0.877765 | 1 |
| [PurviGit/redrob-ranker](https://github.com/PurviGit/redrob-ranker) | reviewer | 0.842987 | 0.842734 | 0.893145 | 0.960592 | 0.954013 | 0.718957 | 0.765056 | 0.872646 | 0.801234 | 0.871866 | 0.956511 | 0.949957 | 0.946997 | 0.815793 | 0.956456 | 0.876596 | 7 |
| [khushii1412/redrob-candidate-ranking](https://github.com/khushii1412/redrob-candidate-ranking) | mean7 | 0.860513 | 0.869063 | 0.849532 | 0.965741 | 0.944823 | 0.733935 | 0.787690 | 0.821300 | 0.862277 | 0.847233 | 0.970230 | 0.939742 | 0.961658 | 0.780287 | 0.951103 | 0.876342 | 5 |
| [garg-khushi/redrob-talentrank-os](https://github.com/garg-khushi/redrob-talentrank-os) | mean7 | 0.856855 | 0.831619 | 0.904501 | 0.958912 | 0.959989 | 0.785332 | 0.789918 | 0.789398 | 0.787154 | 0.882102 | 0.960611 | 0.962549 | 0.964171 | 0.756725 | 0.951979 | 0.876121 | 3 |
| [joyjit-das/redrob-ranker](https://github.com/joyjit-das/redrob-ranker) | blind | 0.841142 | 0.860930 | 0.822307 | 0.964396 | 0.927590 | 0.689335 | 0.833265 | 0.865144 | 0.917958 | 0.800981 | 0.967039 | 0.927463 | 0.956614 | 0.831568 | 0.924918 | 0.875377 | 6 |
| [ganduripranathi02/redrob-ai-ranker](https://github.com/ganduripranathi02/redrob-ai-ranker) | h2,mean7 | 0.875472 | 0.865813 | 0.852570 | 0.959428 | 0.944300 | 0.768571 | 0.787120 | 0.813220 | 0.784020 | 0.836271 | 0.960232 | 0.940673 | 0.955423 | 0.825639 | 0.950633 | 0.874626 | 1 |
| [candyflipgit/redrob-candidate-ranker](https://github.com/candyflipgit/redrob-candidate-ranker) | h2,mean7 | 0.905162 | 0.894118 | 0.824197 | 0.964489 | 0.896352 | 0.854442 | 0.803004 | 0.733925 | 0.892000 | 0.805919 | 0.969799 | 0.901476 | 0.965281 | 0.760598 | 0.946030 | 0.874453 | 11 |
| [devanshuk3/Redrob-Codebase](https://github.com/devanshuk3/Redrob-Codebase) | h2,mean7 | 0.892153 | 0.874879 | 0.873358 | 0.953716 | 0.923816 | 0.762632 | 0.833663 | 0.774668 | 0.883458 | 0.875964 | 0.945098 | 0.908747 | 0.914920 | 0.743579 | 0.946833 | 0.873832 | 12 |
| [Harshdeep47/redrob-candidate-ranking](https://github.com/Harshdeep47/redrob-candidate-ranking) | h2 | 0.878723 | 0.832061 | 0.870675 | 0.899076 | 0.876839 | 0.790291 | 0.836377 | 0.801883 | 0.786938 | 0.875015 | 0.947122 | 0.921287 | 0.935517 | 0.890647 | 0.954657 | 0.873140 | 7 |
| [Palak24Ol/IndiaRuns_DataAndAIChallenge](https://github.com/Palak24Ol/IndiaRuns_DataAndAIChallenge) | reviewer | 0.771238 | 0.760946 | 0.895994 | 0.962081 | 0.933852 | 0.716208 | 0.820913 | 0.874605 | 0.884657 | 0.872752 | 0.964593 | 0.943759 | 0.927392 | 0.815803 | 0.945263 | 0.872670 | 7 |
| [roug047/India_runs_data_and_ai_challenge](https://github.com/roug047/India_runs_data_and_ai_challenge) | h2 | 0.895454 | 0.911593 | 0.841425 | 0.958033 | 0.915664 | 0.700376 | 0.750899 | 0.820078 | 0.870225 | 0.820016 | 0.960611 | 0.911672 | 0.955241 | 0.850607 | 0.925946 | 0.872523 | 7 |
| [Preethamkumarkothakonda/redrob_ai_smart_recruiter](https://github.com/Preethamkumarkothakonda/redrob_ai_smart_recruiter) | blind | 0.864941 | 0.821340 | 0.876887 | 0.955707 | 0.920135 | 0.792794 | 0.656799 | 0.803841 | 0.931914 | 0.856165 | 0.960429 | 0.925774 | 0.937948 | 0.826385 | 0.952272 | 0.872222 | 9 |
| [spg3098-alt/redrob-ranker](https://github.com/spg3098-alt/redrob-ranker) | blind | 0.793731 | 0.746768 | 0.883825 | 0.966844 | 0.933698 | 0.701607 | 0.757296 | 0.830416 | 0.920631 | 0.885439 | 0.966704 | 0.934793 | 0.940005 | 0.905148 | 0.916359 | 0.872217 | 5 |
| [Kirtiraj666/redrob_ranker](https://github.com/Kirtiraj666/redrob_ranker) | mean7 | 0.871055 | 0.820405 | 0.914477 | 0.969628 | 0.923381 | 0.790635 | 0.767064 | 0.760098 | 0.849800 | 0.879337 | 0.973958 | 0.917485 | 0.891256 | 0.810175 | 0.939169 | 0.871861 | 5 |
| [0xSHSH/redrob-talentgraph-ai](https://github.com/0xSHSH/redrob-talentgraph-ai) | reviewer,blind,engineering | 0.836610 | 0.799554 | 0.843422 | 0.966345 | 0.957171 | 0.698693 | 0.732907 | 0.877739 | 0.907832 | 0.815926 | 0.966230 | 0.949903 | 0.943369 | 0.866147 | 0.914101 | 0.871730 | 15 |
| [hemasaini011/redrob-ranker](https://github.com/hemasaini011/redrob-ranker) | blind | 0.793836 | 0.806361 | 0.864623 | 0.947861 | 0.917390 | 0.658754 | 0.857565 | 0.857966 | 0.904350 | 0.848874 | 0.954146 | 0.920372 | 0.931137 | 0.854520 | 0.947842 | 0.871040 | 2 |
| [Disha-Ambhore/india-runs-intelligent-candidate-ranking](https://github.com/Disha-Ambhore/india-runs-intelligent-candidate-ranking) | h2 | 0.893433 | 0.885216 | 0.889267 | 0.909105 | 0.905249 | 0.713110 | 0.782220 | 0.771132 | 0.836117 | 0.888336 | 0.930192 | 0.929519 | 0.941938 | 0.845867 | 0.939382 | 0.870672 | 1 |
| [Ashrua7-7/redrob-caliber](https://github.com/Ashrua7-7/redrob-caliber) | mean7 | 0.865634 | 0.854363 | 0.894050 | 0.957816 | 0.891719 | 0.837205 | 0.854984 | 0.687561 | 0.785280 | 0.885724 | 0.958199 | 0.904778 | 0.944707 | 0.791123 | 0.943435 | 0.870438 | 4 |
| [dhakksinesh/redrob-candidate-ranker](https://github.com/dhakksinesh/redrob-candidate-ranker) | h2 | 0.878909 | 0.831509 | 0.841640 | 0.952238 | 0.927364 | 0.772172 | 0.771819 | 0.808052 | 0.868103 | 0.836143 | 0.955972 | 0.942512 | 0.931239 | 0.798894 | 0.922818 | 0.869292 | 4 |
| [Muheet-Mehraj/redrob-matching-engine](https://github.com/Muheet-Mehraj/redrob-matching-engine) | reviewer,blind | 0.808724 | 0.815875 | 0.837609 | 0.949254 | 0.912158 | 0.644900 | 0.698087 | 0.902902 | 0.966756 | 0.845856 | 0.960410 | 0.936539 | 0.920683 | 0.876516 | 0.933863 | 0.867342 | 6 |
| [harshisingh777/Redrob_CodePhattGya](https://github.com/harshisingh777/Redrob_CodePhattGya) | blind | 0.862320 | 0.837638 | 0.853525 | 0.944052 | 0.902525 | 0.665070 | 0.847265 | 0.820060 | 0.894364 | 0.833020 | 0.950278 | 0.900984 | 0.927965 | 0.788984 | 0.967225 | 0.866352 | 8 |
| [Shristi1611/redrob-intelligent-ranker](https://github.com/Shristi1611/redrob-intelligent-ranker) | blind | 0.847230 | 0.849872 | 0.790584 | 0.947311 | 0.917698 | 0.674958 | 0.736379 | 0.846544 | 0.951557 | 0.795054 | 0.961282 | 0.926156 | 0.927506 | 0.817873 | 0.946331 | 0.862422 | 8 |
| [HimanshuRa0/redrob_candidate_ranker](https://github.com/HimanshuRa0/redrob_candidate_ranker) | h2 | 0.888139 | 0.872911 | 0.866947 | 0.930525 | 0.907381 | 0.786333 | 0.670952 | 0.773116 | 0.830635 | 0.852402 | 0.937626 | 0.909117 | 0.943789 | 0.837105 | 0.899644 | 0.860442 | 5 |
| [nimishaagarwal20/redrob-semantic-ranker](https://github.com/nimishaagarwal20/redrob-semantic-ranker) | h2 | 0.883995 | 0.868919 | 0.856147 | 0.962061 | 0.922204 | 0.702549 | 0.707850 | 0.789309 | 0.762959 | 0.852559 | 0.961868 | 0.913448 | 0.935283 | 0.830637 | 0.922040 | 0.858122 | 5 |
| [madhav1431-create/redrob-candidate-ranker](https://github.com/madhav1431-create/redrob-candidate-ranker) | blind | 0.824981 | 0.817127 | 0.813607 | 0.942957 | 0.953202 | 0.746086 | 0.704943 | 0.851524 | 0.928758 | 0.786372 | 0.939164 | 0.946213 | 0.913745 | 0.762934 | 0.939590 | 0.858080 | 4 |
| [dharanh72-cloud/redrob-ranker](https://github.com/dharanh72-cloud/redrob-ranker) | reviewer | 0.790654 | 0.780858 | 0.863479 | 0.952239 | 0.933881 | 0.635661 | 0.590572 | 0.896583 | 0.882456 | 0.843782 | 0.953338 | 0.932617 | 0.943586 | 0.905210 | 0.926714 | 0.855442 | 12 |
| [poovarasu638178-rgb/redrob-candidate-ranker](https://github.com/poovarasu638178-rgb/redrob-candidate-ranker) | blind | 0.782564 | 0.771930 | 0.812883 | 0.928038 | 0.944001 | 0.746482 | 0.755863 | 0.842859 | 0.896520 | 0.789894 | 0.933209 | 0.943009 | 0.919669 | 0.837970 | 0.926628 | 0.855435 | 0 |
| [HanshikaSahu/RedRob-TalentMatchAI](https://github.com/HanshikaSahu/RedRob-TalentMatchAI) | reviewer,blind | 0.838040 | 0.823672 | 0.807188 | 0.960222 | 0.924195 | 0.641700 | 0.660406 | 0.873369 | 0.966756 | 0.780792 | 0.960427 | 0.915131 | 0.950335 | 0.830822 | 0.891994 | 0.855003 | 4 |
| [rahulx2001/recruitgpt-x](https://github.com/rahulx2001/recruitgpt-x) | engineering | 0.837245 | 0.821105 | 0.829782 | 0.959867 | 0.936455 | 0.722554 | 0.725324 | 0.733989 | 0.857711 | 0.811109 | 0.963177 | 0.908844 | 0.920673 | 0.874805 | 0.904374 | 0.853801 | 16 |
| [Chiranjeevibathula/redrob-ai-candidate-ranking](https://github.com/Chiranjeevibathula/redrob-ai-candidate-ranking) | blind | 0.819171 | 0.799276 | 0.828529 | 0.923561 | 0.918089 | 0.701623 | 0.626675 | 0.862181 | 0.938370 | 0.831982 | 0.947682 | 0.940846 | 0.941202 | 0.787494 | 0.928886 | 0.853038 | 4 |
| [GritHri/Redrob_Hackathon_Solution](https://github.com/GritHri/Redrob_Hackathon_Solution) | reviewer | 0.767082 | 0.764702 | 0.872970 | 0.943440 | 0.902435 | 0.648399 | 0.753466 | 0.885915 | 0.832828 | 0.844259 | 0.922095 | 0.892829 | 0.909129 | 0.906041 | 0.911716 | 0.850487 | 8 |
| [Varshini-R1181/redrob-ranker](https://github.com/Varshini-R1181/redrob-ranker) | reviewer,blind | 0.771551 | 0.718308 | 0.840726 | 0.902915 | 0.900745 | 0.624878 | 0.715544 | 0.886247 | 0.952480 | 0.874826 | 0.932301 | 0.923518 | 0.906508 | 0.929545 | 0.873549 | 0.850243 | 2 |
| [NAMPALLY-PRANAY/redrob_h2s_hackathon](https://github.com/NAMPALLY-PRANAY/redrob_h2s_hackathon) | blind | 0.841852 | 0.839914 | 0.827981 | 0.919990 | 0.911786 | 0.733407 | 0.715936 | 0.780584 | 0.941581 | 0.816031 | 0.906903 | 0.916646 | 0.938610 | 0.733706 | 0.922433 | 0.849824 | 4 |
| [Indira-06-Projects/Smart-Candidate-Ranker](https://github.com/Indira-06-Projects/Smart-Candidate-Ranker) | h2 | 0.891940 | 0.862577 | 0.824888 | 0.936616 | 0.863824 | 0.819020 | 0.717476 | 0.653005 | 0.774601 | 0.853141 | 0.966483 | 0.887910 | 0.952568 | 0.797551 | 0.934257 | 0.849057 | 12 |
| [ammu5406/redrob-intel-ranker](https://github.com/ammu5406/redrob-intel-ranker) | h2 | 0.888102 | 0.891546 | 0.845720 | 0.946577 | 0.893383 | 0.647726 | 0.721515 | 0.787559 | 0.750883 | 0.840988 | 0.948155 | 0.909324 | 0.930644 | 0.800357 | 0.931664 | 0.848943 | 4 |
| [kumarvishal01971/INDIA_runs_Data_and_Ai](https://github.com/kumarvishal01971/INDIA_runs_Data_and_Ai) | h2 | 0.873090 | 0.873543 | 0.803121 | 0.940892 | 0.918267 | 0.726657 | 0.717340 | 0.741034 | 0.852564 | 0.775591 | 0.941105 | 0.911190 | 0.929308 | 0.834759 | 0.878216 | 0.847778 | 2 |
| [Jigar8800/redrob-ai-candidate-ranker](https://github.com/Jigar8800/redrob-ai-candidate-ranker) | blind | 0.858771 | 0.854098 | 0.792404 | 0.914439 | 0.885498 | 0.713749 | 0.734247 | 0.798815 | 0.912584 | 0.795441 | 0.918875 | 0.901536 | 0.930239 | 0.821367 | 0.883185 | 0.847683 | 3 |
| [Kartik-37/India_runs_data_and_ai_challenge](https://github.com/Kartik-37/India_runs_data_and_ai_challenge) | blind | 0.858771 | 0.854098 | 0.792404 | 0.914439 | 0.885498 | 0.713749 | 0.734247 | 0.798815 | 0.912584 | 0.795441 | 0.918875 | 0.901536 | 0.930239 | 0.821367 | 0.883185 | 0.847683 | 3 |
| [vanampranav/RedRob](https://github.com/vanampranav/RedRob) | reviewer | 0.829803 | 0.809499 | 0.801980 | 0.943091 | 0.927648 | 0.705643 | 0.705692 | 0.884638 | 0.755557 | 0.802675 | 0.945769 | 0.932484 | 0.920093 | 0.848402 | 0.890217 | 0.846879 | 6 |
| [vipansh93/India_Runs](https://github.com/vipansh93/India_Runs) | reviewer | 0.768128 | 0.737079 | 0.876040 | 0.910240 | 0.900992 | 0.680490 | 0.642868 | 0.910693 | 0.869029 | 0.868679 | 0.917398 | 0.910861 | 0.903724 | 0.892410 | 0.905537 | 0.846278 | 0 |
| [vipansh93/India_Runs2](https://github.com/vipansh93/India_Runs2) | reviewer | 0.768128 | 0.737079 | 0.876040 | 0.910240 | 0.900992 | 0.680490 | 0.642868 | 0.910693 | 0.869029 | 0.868679 | 0.917398 | 0.910861 | 0.903724 | 0.892410 | 0.905537 | 0.846278 | 4 |
| [Ayushpani/india_runs_hackathon](https://github.com/Ayushpani/india_runs_hackathon) | h2 | 0.878233 | 0.874934 | 0.875169 | 0.949863 | 0.930791 | 0.638227 | 0.675646 | 0.735316 | 0.756033 | 0.875169 | 0.931861 | 0.932223 | 0.959810 | 0.801952 | 0.866549 | 0.845452 | 11 |
| [shikhar1809/Sifter_Redrob_Hackathon](https://github.com/shikhar1809/Sifter_Redrob_Hackathon) | reviewer,blind | 0.796774 | 0.770276 | 0.851100 | 0.872716 | 0.909635 | 0.719058 | 0.747212 | 0.903919 | 0.909096 | 0.844830 | 0.885174 | 0.917692 | 0.909093 | 0.700286 | 0.930231 | 0.844473 | 12 |
| [raviprakash720/India-runs](https://github.com/raviprakash720/India-runs) | reviewer | 0.798377 | 0.789057 | 0.784072 | 0.881731 | 0.904015 | 0.660898 | 0.696061 | 0.889667 | 0.945251 | 0.803624 | 0.887544 | 0.904681 | 0.902133 | 0.857214 | 0.897221 | 0.840103 | 5 |
| [Jothik1506-ai/India-Runs-Hackathon_Team-Dev-DUO](https://github.com/Jothik1506-ai/India-Runs-Hackathon_Team-Dev-DUO) | reviewer | 0.814121 | 0.743975 | 0.821052 | 0.920734 | 0.856309 | 0.711024 | 0.800245 | 0.893592 | 0.743439 | 0.851004 | 0.894111 | 0.872151 | 0.890843 | 0.915187 | 0.868531 | 0.839754 | 10 |
| [Praneetb2929/redrob-ranker](https://github.com/Praneetb2929/redrob-ranker) | h2 | 0.884222 | 0.836553 | 0.818840 | 0.874639 | 0.920243 | 0.672718 | 0.665709 | 0.785706 | 0.810817 | 0.819804 | 0.868623 | 0.940493 | 0.935668 | 0.809654 | 0.895513 | 0.835947 | 1 |
| [ragucreation/india-runs_data_ai](https://github.com/ragucreation/india-runs_data_ai) | h2 | 0.897711 | 0.873699 | 0.826007 | 0.936204 | 0.910736 | 0.717243 | 0.753819 | 0.685967 | 0.622862 | 0.801935 | 0.930679 | 0.901196 | 0.909244 | 0.867019 | 0.869226 | 0.833570 | 7 |
| [rishicodesforfun/India-runs-ats](https://github.com/rishicodesforfun/India-runs-ats) | reviewer | 0.779368 | 0.739751 | 0.833607 | 0.909978 | 0.860545 | 0.608184 | 0.702079 | 0.888400 | 0.913355 | 0.849040 | 0.935119 | 0.875514 | 0.931601 | 0.863648 | 0.809316 | 0.833300 | 9 |
| [bhupesho45/redrob-ai-candidate-ranking](https://github.com/bhupesho45/redrob-ai-candidate-ranking) | reviewer | 0.790277 | 0.733332 | 0.854481 | 0.907064 | 0.842063 | 0.683018 | 0.649529 | 0.897295 | 0.872259 | 0.854733 | 0.902651 | 0.856897 | 0.896280 | 0.861429 | 0.877098 | 0.831894 | 2 |
| [supreethi2730/Redrob-Candidate-Ranker](https://github.com/supreethi2730/Redrob-Candidate-Ranker) | blind | 0.719343 | 0.694889 | 0.834615 | 0.931354 | 0.926517 | 0.778022 | 0.618608 | 0.766647 | 0.913512 | 0.792849 | 0.908989 | 0.918206 | 0.934082 | 0.781928 | 0.930086 | 0.829977 | 2 |
| [thisisgulshanshah/redrob-intelligent-ranking](https://github.com/thisisgulshanshah/redrob-intelligent-ranking) | h2 | 0.889726 | 0.843398 | 0.797582 | 0.943413 | 0.879321 | 0.685555 | 0.721934 | 0.673431 | 0.769237 | 0.752318 | 0.939755 | 0.872831 | 0.956555 | 0.808196 | 0.875714 | 0.827264 | 14 |
| [Mohammadsiraj07/Redrob_Hackathon](https://github.com/Mohammadsiraj07/Redrob_Hackathon) | reviewer | 0.784495 | 0.761183 | 0.801019 | 0.911824 | 0.864959 | 0.614513 | 0.586444 | 0.910498 | 0.942152 | 0.807472 | 0.916058 | 0.869261 | 0.900780 | 0.858216 | 0.877457 | 0.827089 | 11 |
| [vishaal-patil/AI_Hackathon_India_Runs](https://github.com/vishaal-patil/AI_Hackathon_India_Runs) | reviewer | 0.814944 | 0.789686 | 0.834256 | 0.938051 | 0.903454 | 0.497542 | 0.463560 | 0.880668 | 0.888323 | 0.811439 | 0.941535 | 0.903707 | 0.902914 | 0.884993 | 0.873258 | 0.821889 | 4 |
| [EktaBhardwaj7/redrob-TalentGraphAI](https://github.com/EktaBhardwaj7/redrob-TalentGraphAI) | engineering | 0.832123 | 0.663182 | 0.864012 | 0.951753 | 0.924379 | 0.746068 | 0.781577 | 0.478600 | 0.677479 | 0.829095 | 0.953473 | 0.932553 | 0.945860 | 0.789660 | 0.956755 | 0.821771 | 16 |
| [Jatin0Jain/IndiaRunsSubmission-Candidate-Ranker](https://github.com/Jatin0Jain/IndiaRunsSubmission-Candidate-Ranker) | reviewer | 0.802652 | 0.791824 | 0.803860 | 0.902492 | 0.870101 | 0.543323 | 0.665670 | 0.883303 | 0.843439 | 0.800489 | 0.884881 | 0.864990 | 0.901903 | 0.840276 | 0.877382 | 0.818439 | 5 |
| [Drishti84/-redrob_ranker](https://github.com/Drishti84/-redrob_ranker) | blind | 0.775921 | 0.780899 | 0.702769 | 0.923102 | 0.900615 | 0.648962 | 0.682910 | 0.841769 | 0.911176 | 0.685374 | 0.925540 | 0.899475 | 0.865308 | 0.832486 | 0.882785 | 0.817273 | 4 |
| [krishna-yesaswini/redrob-ranker](https://github.com/krishna-yesaswini/redrob-ranker) | reviewer | 0.739747 | 0.737733 | 0.775863 | 0.867462 | 0.868503 | 0.682838 | 0.739620 | 0.877091 | 0.867468 | 0.769739 | 0.872295 | 0.864363 | 0.835448 | 0.876014 | 0.848150 | 0.814822 | 1 |
| [SANKALP9TRIPATHI/Redrob](https://github.com/SANKALP9TRIPATHI/Redrob) | reviewer | 0.729974 | 0.704859 | 0.764436 | 0.911871 | 0.899552 | 0.681927 | 0.584675 | 0.934955 | 0.891392 | 0.765057 | 0.923492 | 0.908466 | 0.824369 | 0.820734 | 0.860275 | 0.813736 | 9 |
| [A-001-byte/Redrob-PMP](https://github.com/A-001-byte/Redrob-PMP) | engineering | 0.832709 | 0.830754 | 0.771126 | 0.902604 | 0.818460 | 0.635086 | 0.622236 | 0.758355 | 0.803685 | 0.804645 | 0.932930 | 0.848697 | 0.923888 | 0.784139 | 0.898452 | 0.811184 | 17 |
| [Ritesh-Routray/India_Runs_Hackathon](https://github.com/Ritesh-Routray/India_Runs_Hackathon) | h2 | 0.882940 | 0.740754 | 0.793674 | 0.939214 | 0.887708 | 0.751344 | 0.755687 | 0.540156 | 0.557899 | 0.761507 | 0.958323 | 0.906964 | 0.956057 | 0.777379 | 0.950299 | 0.810660 | 3 |
| [ranejai954/india-runs-track1-submission](https://github.com/ranejai954/india-runs-track1-submission) | reviewer | 0.726022 | 0.696421 | 0.769893 | 0.914613 | 0.849221 | 0.700743 | 0.682929 | 0.885117 | 0.875357 | 0.752337 | 0.915887 | 0.847216 | 0.909867 | 0.739194 | 0.830472 | 0.806353 | 2 |
| [HarshwardhanBhaskar/india-runs-challenge](https://github.com/HarshwardhanBhaskar/india-runs-challenge) | h2 | 0.911788 | 0.863408 | 0.844115 | 0.890938 | 0.843720 | 0.694281 | 0.744649 | 0.589187 | 0.657735 | 0.874523 | 0.878300 | 0.860704 | 0.805807 | 0.738876 | 0.864096 | 0.804142 | 0 |
| [DSJamwal2004/redrob-ranker](https://github.com/DSJamwal2004/redrob-ranker) | engineering | 0.748622 | 0.723341 | 0.765216 | 0.954340 | 0.862552 | 0.684124 | 0.629274 | 0.818264 | 0.754623 | 0.730615 | 0.925737 | 0.845949 | 0.891809 | 0.712589 | 0.863712 | 0.794051 | 14 |
| [dakshDogra07/redrob-ranker](https://github.com/dakshDogra07/redrob-ranker) | reviewer | 0.751839 | 0.698834 | 0.779819 | 0.857203 | 0.853048 | 0.584606 | 0.521908 | 0.878986 | 0.862110 | 0.770336 | 0.877839 | 0.856937 | 0.867865 | 0.877590 | 0.844832 | 0.792250 | 10 |
| [blunterdecosta123/RedrobAI](https://github.com/blunterdecosta123/RedrobAI) | h2 | 0.876275 | 0.763429 | 0.806936 | 0.844925 | 0.819106 | 0.716677 | 0.491538 | 0.663180 | 0.579469 | 0.870859 | 0.844237 | 0.870339 | 0.854834 | 0.815819 | 0.841979 | 0.777307 | -1 |
| [Vasi1951/redrob-ranking](https://github.com/Vasi1951/redrob-ranking) | blind | 0.837546 | 0.812112 | 0.740138 | 0.799655 | 0.763856 | 0.527996 | 0.534997 | 0.838998 | 0.895719 | 0.721433 | 0.802359 | 0.765839 | 0.782534 | 0.752231 | 0.795128 | 0.758036 | 4 |
| [Ksmashhero06/redrob-intelligent-candidate-ranker](https://github.com/Ksmashhero06/redrob-intelligent-candidate-ranker) | h2 | 0.907746 | 0.879867 | 0.785215 | 0.876799 | 0.772435 | 0.511686 | 0.519019 | 0.583655 | 0.563222 | 0.770037 | 0.879130 | 0.774808 | 0.907936 | 0.780490 | 0.815198 | 0.755150 | 6 |
| [nordak005/redrob-ranker](https://github.com/nordak005/redrob-ranker) | engineering | 0.720398 | 0.641323 | 0.790744 | 0.865917 | 0.891668 | 0.623801 | 0.453529 | 0.692252 | 0.583657 | 0.828149 | 0.830835 | 0.898791 | 0.906463 | 0.715388 | 0.788134 | 0.748737 | 15 |
| [PIYUSH-BHAVSAR/redrob_ranking](https://github.com/PIYUSH-BHAVSAR/redrob_ranking) | h2 | 0.874283 | 0.780159 | 0.744931 | 0.881084 | 0.772403 | 0.724833 | 0.688656 | 0.497284 | 0.230216 | 0.732051 | 0.859163 | 0.754128 | 0.828340 | 0.700273 | 0.849614 | 0.727828 | 7 |
| [irudayajason/RedRob](https://github.com/irudayajason/RedRob) | strong-union tie | 0.630466 | 0.575227 | 0.630368 | 0.772732 | 0.690332 | 0.440430 | 0.548476 | 0.633007 | 0.578879 | 0.643296 | 0.798060 | 0.733856 | 0.744673 | 0.630456 | 0.804849 | 0.657007 | 14 |
| [Atharva7115/Redrob-discovery-engine](https://github.com/Atharva7115/Redrob-discovery-engine) | engineering | 0.594623 | 0.572611 | 0.624771 | 0.811900 | 0.714034 | 0.458446 | 0.362886 | 0.642775 | 0.575751 | 0.628209 | 0.833655 | 0.731945 | 0.787137 | 0.751839 | 0.745008 | 0.655706 | 15 |
| [Tejas1234-biradar/IndiaRuns](https://github.com/Tejas1234-biradar/IndiaRuns) | engineering | 0.522675 | 0.458471 | 0.643533 | 0.738685 | 0.636779 | 0.470990 | 0.418749 | 0.417356 | 0.361280 | 0.641745 | 0.732155 | 0.628452 | 0.667630 | 0.544231 | 0.719295 | 0.573468 | 15 |
| [Sathvikar01/india-runs-ranking](https://github.com/Sathvikar01/india-runs-ranking) | engineering | 0.368096 | 0.303700 | 0.444928 | 0.545751 | 0.501252 | 0.195915 | 0.189286 | 0.524907 | 0.059807 | 0.533295 | 0.539968 | 0.568636 | 0.580334 | 0.461828 | 0.641836 | 0.430636 | 17 |
| [anuraggjena/redrob-ai-challenge](https://github.com/anuraggjena/redrob-ai-challenge) | engineering | 0.541759 | 0.491504 | 0.406212 | 0.475188 | 0.407267 | 0.112017 | 0.109949 | 0.473533 | 0.194854 | 0.399544 | 0.475188 | 0.405569 | 0.427799 | 0.432115 | 0.637622 | 0.399341 | 15 |
| [MrNK2107/India-Runs](https://github.com/MrNK2107/India-Runs) | engineering | 0.127930 | 0.090012 | 0.013556 | 0.012901 | 0.012966 | 0.046066 | 0.027120 | 0.000000 | 0.000000 | 0.013201 | 0.012901 | 0.012901 | 0.000000 | 0.000000 | 0.503792 | 0.058223 | 15 |
| [kumarabhik/redrob-candidate-ranking](https://github.com/kumarabhik/redrob-candidate-ranking) | engineering | 0.046602 | 0.019256 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.015240 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.013324 | 0.006295 | 17 |
| [sahil0m/redrob-hackathon](https://github.com/sahil0m/redrob-hackathon) | strong-union tie | 0.046602 | 0.019256 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.015240 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.013324 | 0.006295 | 14 |
| [sandipan-ds/redrob_project](https://github.com/sandipan-ds/redrob_project) | engineering | 0.046602 | 0.019256 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.015240 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.013324 | 0.006295 | 16 |

### Engineering leaders without a valid 100-row artifact

| Repository | Selected for | Engineering score | Updated |
|---|---:|---:|---:|
| [akashchaudhary5812-oss/INDIA_RUNS_DATA_AI_CHALLENGE](https://github.com/akashchaudhary5812-oss/INDIA_RUNS_DATA_AI_CHALLENGE) | engineering | 15 | 2026-06-17T06:00:35Z |
| [dhruv-sanan/redrob-ranker](https://github.com/dhruv-sanan/redrob-ranker) | engineering | 14 | 2026-06-28T20:51:17Z |
| [innocentgaming/redrob-ai-ranker](https://github.com/innocentgaming/redrob-ai-ranker) | engineering | 15 | 2026-06-27T20:05:59Z |
| [kishan-42069/Redrob](https://github.com/kishan-42069/Redrob) | strong-union tie | 14 | 2026-06-28T16:41:46Z |
| [MoulendraBalaji/IndiaRuns-Intelligent-Candidate-Discovery-Ranking-System](https://github.com/MoulendraBalaji/IndiaRuns-Intelligent-Candidate-Discovery-Ranking-System) | engineering | 15 | 2026-06-28T18:11:30Z |
| [Narayan1006/VireHire](https://github.com/Narayan1006/VireHire) | engineering | 15 | 2026-06-01T17:57:48Z |
| [ronak-ravtode/redrob-ranker](https://github.com/ronak-ravtode/redrob-ranker) | engineering | 15 | 2026-06-25T12:30:52Z |
| [Shreekumar-Shah-AICTE/project-trinetra](https://github.com/Shreekumar-Shah-AICTE/project-trinetra) | engineering | 15 | 2026-06-28T19:36:53Z |
| [sidinsearch/redrob](https://github.com/sidinsearch/redrob) | engineering | 15 | 2026-06-22T05:00:50Z |

## Machine-readable files

- [`full_comparison_matrix_2026-06-29.csv`](../experiments/full_comparison_matrix_2026-06-29.csv) - every component for main, V3, V4, and all 99 valid strongest-union repositories.
- [`full_comparison_summary_2026-06-29.json`](../experiments/full_comparison_summary_2026-06-29.json) - local metrics, public ranks, integrity, runtime, overlaps, and census metadata.

## Limits

- These are proxy labels, not Redrob hidden ground truth.
- Public artifacts are selected by their best H2 CSV per repository, so this comparison is intentionally favorable to competitors.
- Reviewer and blind sets have low top-100 coverage; treat their specialist ranks as directional.
- Engineering score measures repository completeness, not ranking quality.
- The six extra frozen evaluators were computed for the 99 strongest-union artifacts, not all 672 valid public outputs.
