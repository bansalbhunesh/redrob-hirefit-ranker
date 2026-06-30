# Excluded Artifacts

What was deliberately NOT merged into the integration branch, and why. (Most were already
`.gitignore`d on the research branches, so they were never in any tree; listed here for a
complete audit trail.)

| Artifact | Category | Reason excluded |
|---|---|---|
| `experiments/_pool.pkl` (~27 MB) | C | regenerable cache (`_build_pool.py`); contains candidate data |
| `docs/human_opinion/raw_hn_corpus.jsonl`, `raw_phi2_corpus.jsonl` | C | full retrieved corpora; regenerable via `phi_collect.py`; only short coded excerpts are kept |
| `experiments/fusion_raw_submission.csv`, `constrained_submission.csv` | C | research submissions; regenerable; never the official output |
| `experiments/omega_outputs/omega_submission.csv` | C | research ranking; gitignored; regenerable |
| `experiments/_competitor_extract.py` | D | contains competitor repo names; local research tool (gitignored) |
| `experiments/disagreement_set/reviewer_packet.jsonl`, `anon_key.json` | C/D | candidate profile text + scoring key; kept local only |
| `experiments/psi_panel/reviewer_packet.jsonl`, `anon_key.json` | C/D | same — Ψ packet is local; only the manifest (ids+hash) is committed |
| `C:/Users/bhune/_cx/`, `_sweep/` (local scratch) | D | cloned-competitor scoring scratch outside the repo |
| any cloned competitor repositories | D | ToS; cloned one-at-a-time then deleted (disk-safe); never stored |
| `codex/*`, `feature/*`, `wip/*` branches' code | D | pre-program perf/infra; not part of the decision arc; left isolated |

## Never merged (hard rules honored)
- No experimental ranking change that would alter golden.
- No simulated reviewer output presented as human evidence (Ω labelled SIMULATED; Ψ `AWAITING_HUMAN_DATA`).
- No self-coded "second coder" passed off as intercoder reliability (`AWAITING_SECOND_CODER`).
- No secrets/tokens/local absolute paths in committed files.
- No raw personal data beyond hashed authors + short public excerpts.
