# Pre-Submission Checklist — Redrob HireFit Ranker

Everything controllable, in one place. ✅ = done & verified in-repo. 🔲 = needs you (I can't do it).

## ✅ Done & verified (in the repo)

- **Submission locked:** V6 battle-proof release, frontier-v5 ranking core, SHA-256 `8f7f30c6…`.
- **One release path:** `PYTHONHASHSEED=0 python rank.py --release ...` forces the champion and fails
  closed on truncation, alternate models/backends, corrupt input/model artifacts, wrong counts,
  nondeterministic thread settings, or output hash drift.
- **Reproducible:** `./reproduce.sh` green; full 100K Docker release is byte-identical and atomic;
  forced OOM preserves the old output and leaves no mounted temporary artifact.
- **Tests:** 262 passed, 6 environment skips; configuration, input artifact, model artifact, output, numeric, and supply-chain gates prevent drift.
- **Constraints:** CPU-only, offline, deterministic; **136.0 s pipeline / 149.1 s wall** at 2 CPU /
  16 GiB; sampled peak 4.13 GiB; 0 honeypots in top-100 (53 detected).
- **Supply chain:** digest-pinned base, SHA-256-pinned wheels, `pip --require-hashes`, and no known
  production dependency vulnerabilities in the 2026-06-30 `pip-audit` pass.
- **Validation:** 30/30 composite wins over main; #1 / 673 mean7; #1 / 100 mean15; #3 / 322
  balanced4; 883 safety fusions; 100 repeated half-splits; external reviewer and blind slices.
- **Surfaces consistent & polished:** README (story, TOC, 2 SVG diagrams, live-demos section,
  results data), `SHIPPING_DECISION`, `REPRODUCTION`, `why_this_wins`, deck (PPTX+PDF, 33 features),
  both frontends (contrast fixed, documented in `READABILITY_AUDIT.md`), dashboard, metrics_manifest.
- **Live demos rebuilt:** HF Space (`huggingface.co/spaces/bansal1234/Hirefit`) and Render
  (`redrob-hirefit-ranker.onrender.com`) both returning 200 on latest commits.

## 🔲 Needs you (the highest-leverage remaining items)

1. 🔲 **Confirm the GitHub repo is PUBLIC after the V6 push.** A judge who cannot open it cannot score it.
2. 🔲 **Record the 2-minute V6 demo video** and paste the link into the README "Live demos & video"
   slot and the deck. On a rigor/holistic rubric this moves the needle more than any code change.
3. 🔲 **Refresh the live screenshots** (`docs/assets/render_pipeline.png`, `hf_space_upload.png`)
   from the rebuilt sites so the README shows the fixed contrast, not the pre-fix captures.
4. 🔲 **Rotate the aicredits API key** — it appeared in chat history.
5. 🔲 **Confirm the already-submitted portal entry references the public repository and exact
   `8f7f30c6…` CSV.** The Track 1 deadline was June 28; do not assume a late portal replacement is accepted.
6. 🔲 **Final eyeball** of the live HF Space + Render after rebuilds (hard-refresh) to confirm every
   label/number reads as intended.

## Honest note on ranking

Official labels and numeric judging weights are unpublished. The transparent mission-derived
positioning score is 93.7/100, projected #1 with an honest #1–#3 range; it is not an official result.
The controllable edge is the combination of ranking quality, contextual evidence, behavioral signals,
speed, reproducibility, integrity, explainability and presentation.
