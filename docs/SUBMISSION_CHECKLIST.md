# Pre-Submission Checklist — Redrob HireFit Ranker

Everything controllable, in one place. ✅ = done & verified in-repo. 🔲 = needs you (I can't do it).

## ✅ Done & verified (in the repo)

- **Submission locked:** `frontier-v5` `submission.csv`, SHA-256 `8f7f30c6…`; V6 keeps its exact order.
- **One release path:** `PYTHONHASHSEED=0 python rank.py --release ...` forces the champion and fails
  closed on truncation, alternate models/backends, corrupt artifacts, wrong counts, or hash drift.
- **Reproducible:** `./reproduce.sh` green; full 100K Docker release is byte-identical and atomic.
- **Tests:** 240 passed, 6 environment skips; configuration, artifact, output, numeric, and supply-chain gates prevent drift.
- **Constraints:** CPU-only, offline, deterministic (`PYTHONHASHSEED=0`); ~80s cloud / ≤300s budget;
  peak ~6.1 GB / 16 GB; 0 honeypots in top-100 (53 detected).
- **Supply chain:** digest-pinned base, SHA-256-pinned wheels, `pip --require-hashes`, and no known
  production dependency vulnerabilities in the 2026-06-30 `pip-audit` pass.
- **Validation:** two-study (golden vs hedge, holdout) + two cross-family judges (gpt-4.1 +0.0197,
  gemini-2.5-pro +0.0160) + post-decision stress test (rrf-lock30 challenge → hedge held).
- **Surfaces consistent & polished:** README (story, TOC, 2 SVG diagrams, live-demos section,
  results data), `SHIPPING_DECISION`, `REPRODUCTION`, `why_this_wins`, deck (PPTX+PDF, 33 features),
  both frontends (contrast fixed, documented in `READABILITY_AUDIT.md`), dashboard, metrics_manifest.
- **Live demos rebuilt:** HF Space (`huggingface.co/spaces/bansal1234/Hirefit`) and Render
  (`redrob-hirefit-ranker.onrender.com`) both returning 200 on latest commits.

## 🔲 Needs you (the highest-leverage remaining items)

1. 🔲 **Make the GitHub repo PUBLIC.** It currently 404s to anyone but you — a judge who can't open
   it cannot score it. **Single biggest unforced loss; do this first.**
2. 🔲 **Record the 2-minute demo video** and paste the link into the README "Live demos & video"
   slot and the deck. On a rigor/holistic rubric this moves the needle more than any code change.
3. 🔲 **Refresh the live screenshots** (`docs/assets/render_pipeline.png`, `hf_space_upload.png`)
   from the rebuilt sites so the README shows the fixed contrast, not the pre-fix captures.
4. 🔲 **Rotate the aicredits API key** — it appeared in chat history.
5. 🔲 **Upload `submission.csv` to the official portal** exactly per the competition's instructions
   (format/filename), and confirm acceptance before the **June 28** deadline.
6. 🔲 **Final eyeball** of the live HF Space + Render after rebuilds (hard-refresh) to confirm every
   label/number reads as intended.

## Honest note on ranking

Quality on the hidden labels is label-bound (proven: ~0.878 ceiling for every method we tried; the
gap is label information we can't access). This submission's edge is **rigor, reproducibility,
integrity, and explainability** — strongest on a holistic rubric, capped on a pure-score one. The
items above are the controllable factors that decide whether a judge ever *sees* that edge.
