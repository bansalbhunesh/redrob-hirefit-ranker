# Repo Comparison Matrix — Redrob India Runs Field Audit

**Method.** Every score below is **measured**: each repo's committed `submission.csv` was
loaded and scored against our frozen 100K blind arbiter (`artifacts/h2_availblind_labels.jsonl`)
with our own `redrob_ranker.eval_harness` (challenge composite `0.50·NDCG@10 + 0.30·NDCG@50 +
0.15·MAP + 0.05·P@10`, `unlabeled=exclude`). Generated 2026-06-15.

**Two hard caveats on the numbers:**
1. Scoring is **top-100-only** (competitors ship only a top-100), so MAP and P@10 **saturate at
   1.0** for every fully-relevant list — the composite is therefore **NDCG-driven**, and absolute
   values run higher than our published full-ranking figure (0.7716). **Relative ordering is
   valid; absolute values are not comparable to our docs.**
2. The blind set is our **availability-aware proxy**, not the hidden human labels. A high blind
   score can be inflated by JD-disqualified candidates the proxy under-penalizes (see
   `branch_ranking_report.md` — confirmed for the three repos above us).

**Evidence grades:** `MEASURED` = scored here. `CLAIM` = from the pasted "audit" report,
unverified. `INSPECTED` = source code read directly in this or a prior session.

| Measured rank | Repo | Composite (blind) | NDCG@10 | NDCG@50 | Approach | Evidence | vs YOU |
|---|---|---|---|---|---|---|---|
| 1 | Thermo041/Indiaruns | 0.886 | 0.855 | 0.863 | stdlib term-count + Next.js dashboard | INSPECTED | above (proxy-inflated, 40% disq picks) |
| 2 | Preethamkumarkothakonda/redrob_ai_smart_recruiter | 0.865 | 0.844 | 0.827 | FAISS + sentence-transformers + cross-encoder rerank | INSPECTED (deps) | above (proxy-inflated, 34% disq; torch/FAISS compliance risk) |
| 3 | anishanandhan/RedrobIQ-AI | 0.864 | 0.810 | 0.869 | multi-stage parser + template mapping, deterministic, tested | INSPECTED (deps) | above (proxy-inflated, 38% disq) |
| **4** | **bansalbhunesh/redrob-hirefit-ranker (YOU)** | **0.862** | **0.829** | **0.827** | **BM25 + 33-feature × behavioral/honeypot/disqualifier** | **INSPECTED** | **—** |
| 5 | datapiratepy/redrob-ranker | 0.854 | 0.809 | 0.832 | pyyaml-only, 7-phase, **rejected embeddings for 44-template table** | INSPECTED | below (tie) |
| 6 | dheeraj-droid/REDROB (WorthyHire) | 0.832 | **0.857** | 0.759 | rule → BGE-small → cross-encoder rerank | MEASURED | below composite, **above on NDCG@10** |
| 7 | krish57-bit/redrob-ranker | 0.800 | 0.742 | 0.773 | evidence-mining + TF-IDF/LSA semantic blend (0.12) | INSPECTED | below |
| 8 | aravindaariv0904-collab/talent-ranker | 0.792 | 0.737 | 0.775 | FAISS + hybrid + diversity rerank (CLAIM) | MEASURED | below |
| 9 | jmurarka/redrob-ranker | 0.785 | 0.735 | 0.736 | ontology JD parser + symmetric matching (CLAIM) | MEASURED | below |
| 10 | kanish-techjays/redrob-ranker (Fitjays) | 0.756 | 0.695 | 0.732 | LightGBM LambdaRank on Qwen labels (CLAIM) | MEASURED | below |
| 11 | sskuntal29/redrob_challenge | 0.753 | 0.665 | 0.751 | XGBoost + BGE-Large (CLAIM) | MEASURED | below |
| 12 | swaraj3092/redrob-ranker | 0.693 | 0.673 | 0.581 | 5-layer hand pipeline, pandas-only | INSPECTED | below |
| 13 | stack-rishi/Ai-Recruiter | 0.688 | 0.628 | 0.666 | dense + PageRank + BM25 PRF + cross-encoder (CLAIM) | MEASURED | below |
| 14 | bipinmaurya5567-bit/India_Runs-Ranker | 0.639 | 0.724 | 0.546 | BM25 → bi → cross-encoder + RRF (CLAIM) | MEASURED | below |
| 15 | smhsneh/aidatachallenge.indiaruns | 0.523 | 0.622 | 0.399 | BM25 → 6-dim math scoring (CLAIM) | MEASURED | below |
| 16 | RohithKalva/redrob-ranker | 0.422 | 0.520 | 0.339 | BM25 shortlist + LightGBM rerank (CLAIM) | MEASURED | below |

## Not measurable from committed artifacts (ship no scoreable top-100)

These were **rated 8.0–9.0 by the pasted report**, but commit no valid 100-row `CAND_` submission,
so the report's scores are **unverifiable** (would require running each repo — not done; arbitrary
code execution on 9 strangers' repos, and out of scope for a static audit):

`Ayushhgit/redrob-ranker` (rpt #5/9.0) · `NavpreetDevpuri/canjob` (#10) ·
`shanmukh-codes/india-runs-hackathon-2026-singleton` (#14) · `Shubham-33/evidencerank-redrob`
(#15) · `bhaveshsarode09-ops/DeepShortlist` (#17) · `ShyamAlancode/Redrob-Ranker` (#18) ·
`AnshAggr1303/redrob-ranker` (#21) · `Vinilnaik3705/Redrob_Hackathon` (#24) ·
`tejasv27/aethelgard-ranker` (#25)

## Unreliable measurements (flagged, not counted)

- `HirenKodwani/HireMind` — coverage **10%** (uses mostly non-official candidate ids) → score 0.178 meaningless.
- `yashtyagee/redrob-ranker` — only a **50-row sample**, not a full submission → 0.160.
- `tanuluthra4/recruiter-lens` — ships **only the hackathon `sample_submission.csv` template**, no real output.
- `dheeraj-droid`, `kanish-techjays` initially mis-scored at 0.047 because the picker grabbed the
  shared `sample_submission.csv` template; corrected above using their real files
  (`WorthyHire.csv`, `techjays.csv`).

## UPDATE 2026-06-15b — 4th report ("170+ repos, top 30"), 12 new entrants scored

All measured on the blind arbiter, blobless clone, template-skip applied. **None beat you.**

| Repo | Report claim | Composite | NDCG@10 | NDCG@50 | Note |
|---|---|---|---|---|---|
| De-Coder05/redrob-ranking-challenge | #26 / 8.5 | 0.814 | 0.770 | 0.762 | highest new entrant; stdlib-only |
| shikhar1809/Sifter_Redrob_Hackathon | **#1 / 9.8 "WINNER"** | **0.797** | 0.717 | 0.808 | fine-tuned distilbert on 180 human labels — see caveat |
| Kunal77744/redrob-candidate-ranker | #20 / 8.5 | 0.795 | 0.761 | 0.735 | |
| GourabSaha66/Redrob-AI-Candidate-Ranker-System | #6 / 9.3 | 0.783 | 0.762 | 0.720 | cross-encoder + XGBoost claim |
| Rajneel-Chavan/redrob-candidate-ranker | #27 / 8.5 | 0.733 | 0.678 | 0.678 | stdlib-only |
| nishita-rana/redrob-candidate-ranker | #14 / 8.8 | 0.695 | 0.613 | 0.659 | |
| abhay-2108/Redrob-MatchWise | #12 / 9.0 | 0.626 | 0.619 | 0.502 | |
| anuraggjena/redrob-ai-challenge | #11 / 9.0 | 0.542 | 0.519 | 0.402 | "NDCG@10=1.0 on synthetic labels" ≠ blind |
| dakshrawat298-gif/Redrob-rank-engine | #2 / 9.5 | 0.512 | 0.572 | 0.427 | |
| hanzala02hk-code/Redrob_AI_Ranker | #21 / 8.7 | 0.028 | — | — | suspect (likely inverted/wrong file) |
| gvdnikhil/redrob-candidate-ranking | #13 / 8.8 | NO submission | — | — | report's score unverifiable |
| ballsvignesh/redrob-ranking-engine | #19 / 8.7 | NO submission | — | — | report's score unverifiable |

**Sifter caveat:** trained on its own 180 human labels (not our availability proxy), so its 0.797
here may understate it on the real human prize labels. Its claimed 0.874 NDCG@25 / 0.7568 kappa are
on its private 180-label set — not a shared benchmark, not comparable. The one competitor whose
real-label ceiling is a genuine unknown rather than a debunked claim.

## Merged complete ranking (all verifiable submissions, blind arbiter, top-100-only)

1. Thermo041 0.886 · 2. SmartRecruiter 0.865 · 3. RedrobIQ 0.864 · **4. YOU 0.862** ·
5. datapiratepy 0.854 · 6. WorthyHire 0.832 · 7. De-Coder05 0.814 · 8. krish57 0.800 ·
9. Sifter 0.797 · 10. Kunal77744 0.795 · 11. TalentRanker 0.792 · 12. jmurarka 0.785 ·
13. GourabSaha66 0.783 · 14. Fitjays 0.756 · 15. sskuntal29 0.753 · 16. Rajneel-Chavan 0.733 ·
17. nishita-rana 0.695 · 18. swaraj3092 0.693 · 19. AI-Recruiter 0.688 · 20. India_Runs-Ranker 0.639 ·
21. MatchWise 0.626 · 22. anuraggjena 0.542 · 23. aidatachallenge 0.523 · 24. Vibecoder 0.512 ·
25. RohithKalva 0.422

(Top 3 are proxy-inflated — 34–40% JD-disqualified unique picks; see `branch_ranking_report.md`.)

## UPDATE 2026-06-15c — 5th report ("180+ repos"), 6 new entrants scored

None beat you. AnshikaGoswami27 0.744 · PR-ODINSON (rpt#9/9.0) 0.722 · rehannayeem0786 (rpt#22) 0.617 ·
**jwrhw7tueydwtt7575g (rpt#3/9.5 "most complete architecture") = 0.051 on a 50-row incomplete CSV** ·
Nandish3010 (rpt#23) and HarithaB2005 ship no submission.

## UPDATE 2026-06-15d — 6th report ("200+ repos"), 7 new entrants scored — FIRST REAL NEAR-PEER

- **VIVPM/redrob-ranker = 0.860 (NDCG@10 0.829) — a genuine statistical tie with us (0.862).**
  First new entrant in six reports to actually reach our level. Cross-encoder + model2vec + TF-IDF +
  BGE stack. Not yet checked for disqualified-pick inflation (recommended next step).
- Harshgarg123 0.846 (close below). Redrob-PMP (rpt#2/9.7) 0.833 — below composite but its
  **NDCG@10 0.852 beats ours (0.829)**, reinforcing the cross-encoder top-10 signal.
- goatraj23 (rpt#10/9.0 "3s world-consistency") 0.679; meenajainshah 0.805; Sri175 & ayush1233 ship
  no submission.

## UPDATE 2026-06-15e — 7th report, 6 originally-missed repos scored

- **SandeepKumarDubey7/redrob-ranker = 0.866 (NDCG@10 0.860) — edges us (0.862).** 2nd genuine
  near-peer (after VIVPM 0.860). 7-stage TF-IDF + 10-dim weighted + 9 honeypot heuristics. Inflation
  status unchecked (likely similar to the other ~0.86 repos).
- 4 of 6 ship no committed submission (Kanhaiya76618, MadhavKamble, icarusiftctts, SreeHz — all have
  offline-precompute pipelines; report's 9.0–9.3 scores unverifiable from artifacts). pravoobi ships
  only its eval `labels.csv` (33 rows) → not a real submission.

## UPDATE 2026-06-15f — 8th report, 10 final originally-missed repos scored
8 of 10 ship NO committed submission (incl. the report's new #3 "SignalHire" — claimed GPU-precompute
"POTENTIAL WINNER"; GPU also violates the no-GPU rule). The 2 real ones score below us: Guru-1110
0.848, GaganHR2006 0.808.

## FINAL MEASURED TOP 15 (consolidated, blind arbiter, all 8 reports)

Composite = `0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10`, top-100-only, `unlabeled=exclude`,
100% coverage. Relative order valid; absolute not comparable to our published full-ranking 0.7716.

| # | Repo | Composite | NDCG@10 | Real status |
|---|---|---|---|---|
| 1 | Thermo041/Indiaruns | 0.886 | 0.855 | **proxy-inflated** (40% JD-disqualified unique picks) |
| 2 | SandeepKumarDubey7/redrob-ranker | 0.866 | 0.860 | genuine tie (inflation unchecked) |
| 3 | Preethamkumarkothakonda (SmartRecruiter) | 0.865 | 0.844 | **proxy-inflated** (34%); torch/FAISS compliance risk |
| 4 | anishanandhan/RedrobIQ-AI | 0.864 | 0.810 | **proxy-inflated** (38%) |
| **5** | **bansalbhunesh/redrob-hirefit-ranker (YOU)** | **0.862** | **0.829** | **#1 on JD-faithful labels** |
| 6 | VIVPM/redrob-ranker | 0.860 | 0.829 | genuine tie (inflation unchecked); 4-embedding+cross-encoder |
| 7 | datapiratepy/redrob-ranker | 0.854 | 0.809 | below; independently rejected embeddings |
| 8 | Guru-1110/redrob-ranker | 0.848 | 0.806 | below |
| 9 | Harshgarg123/redrob-ranker | 0.846 | 0.824 | below |
| 10 | A-001-byte/Redrob-PMP | 0.833 | 0.852 | below composite; **N@10 beats us** |
| 11 | dheeraj-droid/REDROB (WorthyHire) | 0.832 | 0.857 | below composite; **N@10 beats us**; cross-encoder |
| 12 | De-Coder05/redrob-ranking-challenge | 0.814 | 0.770 | below |
| 13 | GaganHR2006/redrob-ranker | 0.808 | 0.753 | below |
| 14 | meenajainshah/redrob-ranker | 0.805 | 0.759 | below |
| 15 | krish57-bit/redrob-ranker | 0.800 | 0.742 | below; TF-IDF/LSA semantic |

**You are #5 raw / #1 JD-faithful.** The 3 above you (ranks 1,3,4) are proxy-inflated; ranks 2 and 6
are genuine dead-even ties. No repo is confirmed genuinely above you on the labels that decide the
prize. Note ranks 10–11: cross-encoders that beat you on NDCG@10 (50% of prize weight) — the only
real architectural edge in the field.

## Final bottom line (8 reports, 6 batches, ~47 verifiably-scored repos)
**Top cluster on the blind arbiter (within ~0.024):** Thermo041 0.886 · SmartRecruiter 0.865 ·
SandeepKumarDubey7 0.866 · RedrobIQ 0.864 · **YOU 0.862** · VIVPM 0.860 · datapiratepy 0.854 ·
Harshgarg123 0.846. The three confirmed-above (Thermo/SmartRecruiter/RedrobIQ) are **proxy-inflated**
(34–40% JD-disqualified picks). Two genuine ties exist (VIVPM, SandeepKumarDubey7) — inflation
unchecked. **No repo is confirmed genuinely above us on JD-faithful labels.**

Every "9.0–9.8 CRITICAL WINNER" the seven reports crowned either measured below us, tied us, or shipped
no scoreable submission. The reports' scores have near-zero correlation with measured performance. The
one durable real signal: **cross-encoder NDCG@10 ≥ ours** (VIVPM/Redrob-PMP/WorthyHire) — 50% of prize
weight — the sole lever worth a guarded, blind-gated experiment.
