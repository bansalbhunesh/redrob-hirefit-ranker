# Ablation Ladder (Phase 3)

Dev slice: first 20,000 candidates; top-100 per rung; shared harness
(`src/redrob_ranker/eval_harness.py`), policy=exclude; composite = challenge
formula `0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10`.

**Primary metric: the independent-heuristic composite** — it labels all 100K
candidates, so every rung is scored on its full top-100. The LLM-judge column
is shown for transparency but is **not comparable across rungs** here: its 249
labels were sampled around the full-pool submission, so a 20K-slice top-100 is
only 25–32% covered and the exclude policy scores each rung on a different,
selection-biased sub-sample.

| rung | composite (independent, full coverage) | delta | LLM judge (cov) |
|---|---|---|---|
| 1. naive JD-keyword count (the strawman) | 0.6128 | — | 0.6753 (25%) |
| 2. BM25 only | 0.7158 | **+0.1030** | 0.6984 (26%) |
| 3. BM25 + 28-feature recruiter matrix (multipliers off) | 0.7671 | **+0.0513** | 0.7690 (32%) |
| 4. full system: + behavioral/honeypot/disqualifier multipliers (shipped) | 0.7831 | **+0.0160** | 0.6934 (31%) |
| 5. + dense embeddings | — | tested, **rejected**: NDCG@10 +0.0000, ~2.2× runtime | (recorded gate, `artifacts/embedding_gate_result.txt`; not re-run) |

Reading the ladder:

- **Keywords → BM25 (+0.103):** real lexical ranking with phrase/concept
  expansion beats raw keyword counting by a wide margin.
- **BM25 → features (+0.051):** the 28-feature recruiter matrix (career
  evidence, production signals, logistics) adds the next-largest gain.
- **Features → multipliers (+0.016):** the guardrails add a further measured
  gain on graded labels — and, beyond composite, they are what keeps all 53
  hard honeypots and the keyword-stuffer traps out of the top-100 (rung 3
  alone has no such protection).
- **Embeddings:** measured zero quality gain at ~2.2× runtime → rejected; the
  negative result is the defense.

Rung 4 is the shipped configuration by construction (same `rank_candidates`
code path and default config; the full-pool equivalent reproduces the golden
submission hash).
