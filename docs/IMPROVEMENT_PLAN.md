# Winner-Grade Improvement Plan (phased)

Goal: make every surface judge-flawless — readable, fast, fully documented, every link live, every
number consistent — without ever touching the frozen production ranking or the shipped submission.
Executed in ordered phases (not one sweep); each phase ends green (tests + push).

## Current-state findings (audit 2026-06-16)

- **Contrast/readability (both frontends).** Dim text on dark navy is hard to read: the
  integrity-disclaimer paragraph, the italic *detector-flagged anomaly* (nearly invisible), the
  upload-box label, search/filter labels, the HF "Download full ranked CSV" button (mint-on-mint),
  and footers. Root token: `--text-muted: #94A3B8` (too low), plus dimmer inline `<em>`/placeholder
  styles.
- **Stale UI number.** Render pipeline diagram shows **"28-D Features"** (JS `PIPELINE_STAGES`) —
  must be 33 to match the shipped scorer.
- **README gaps.** No table-of-contents/index with anchors; no embedded screenshots (Render / HF /
  dashboard); no architecture diagram (mermaid); no demo-video slot; no Render demo link; spacing
  can be tightened for clarity. (All 12 internal doc links currently resolve.)
- **Pipeline speed.** Worst-case ~193s / typical ~80–125s — under budget but not optimized; user
  wants a "why is it slow" pass and a safe speedup before re-measuring.
- **Tests/research debt.** Backend API routes, frontend routes, and pipeline have room for more
  coverage; runtime/values must be re-tested after any speedup.

## Hard invariants (every phase)

1. `rank.py` / `src/redrob_ranker/` reproduce golden `af8f2b32` byte-for-byte (slice gate + full 100K).
2. Shipped `submission.csv` stays the hedge `24f84f4b` (or is regenerated deterministically).
3. Full suite green; no fabricated numbers; `metrics_manifest.json` is the single source of truth.
4. No API key in any commit; HF Space commits authored as `bansalbhunesh`.

---

## Phase 1 — Frontend readability & correctness  (both surfaces)
**Objective:** every piece of text passes a comfortable-contrast bar on dark; no stale UI numbers.
- Raise `--text-muted` to a legible slate (≈ `#B8C4D9`+) and add a `--text-dim`/`--text-faint` scale
  with documented contrast ratios; fix the `<em>` *detector-flagged anomaly*, upload label,
  search/filter labels, HF "Download CSV" button, and footers specifically.
- Render: `PIPELINE_STAGES` "28-D Features" → "33 Features".
- Verify token contrast vs `#0F172A` (target WCAG AA ≥ 4.5:1 for body, ≥ 3:1 for large/labels).
- Ship: Render via repo; HF via submodule (push to HF). Re-screenshot for the README (Phase 4).
**Done when:** no dim-on-dark text remains; "33" everywhere; both demos legible end to end.

## Phase 2 — Pipeline performance (why slow → faster → re-measure)
**Objective:** explain the runtime honestly and shave it without changing output one byte.
- Profile `run_ranking` on the 100K pool (cProfile / per-stage timers): BM25 build, feature
  extraction, tokenization, sort. Identify the dominant cost.
- Apply only **byte-identical** speedups (vectorize, hoist, cache, avoid recompute); gate every
  change with the 2k slice + full-100K hash.
- Re-measure native + docker `--cpus=2 --memory=16g`; update `metrics_manifest.runtime` and every
  surface from it. Document the "why it was slow / what we changed" in `docs/performance_audit.md`.
**Done when:** golden still byte-identical, new numbers measured and propagated, write-up added.

## Phase 3 — Backend / frontend / routes tests & remaining research
**Objective:** close coverage gaps the user flagged.
- Enumerate API routes (FastAPI) → assert each has a test (status, error paths, no-leak-on-500,
  payload shape). Add missing ones.
- Frontend: smoke/lint the static app (no console errors, all stages render, upload→rank→download).
- Sweep `experiments/` for any un-run/un-recorded research; record or retire.
**Done when:** every route tested, frontend smoke green, research ledger has no loose ends.

## Phase 4 — README as a hackathon-winning document
**Objective:** extreme clarity, navigable, visual.
- **Index/TOC** with clickable anchors to every section.
- Tighten spacing; add sections as needed (e.g., "At a glance", "Architecture", "Live demos",
  "Results & graphs", "Validation", "Reproduce", "FAQ").
- **Architecture diagram** (mermaid) + the pipeline + the decision/validation flow.
- **Embedded visuals:** Render screenshot, HF Space screenshot, dashboard screenshot (Phase-1
  refreshed, true colors) under `docs/assets/`.
- **Demo-video slot** (placeholder + link) and **Render live link** alongside the HF badge.
- Graphs/data: golden-vs-hedge deltas, runtime matrix, measured-negatives — as tables/figures.
**Done when:** README reads top-to-bottom as a polished story, every section reachable from the TOC,
visuals present, video slot ready.

## Phase 5 — Links & all-surface consistency sweep
**Objective:** nothing dead, nothing inconsistent.
- Verify every link/badge/anchor (README, docs, deck, frontends) resolves; fix the study/demo links.
- Re-run the numeric audit (tests=198, 33 features, hashes, runtime, hedge figures) across README,
  docs, deck, both frontends, dashboard, manifest.
**Done when:** zero broken links, zero numeric drift (guarded by the manifest test).

## Phase 6 — Final validation & "best of best"
**Objective:** prove it.
- Full suite, `reproduce.sh`, docker constrained run; refresh screenshots; final commit/push.
- Confirm demo-video slot + links ready for the user to drop the recording in.
**Done when:** all green, all pushed, README/deck/demos camera-ready.

---

## Sequencing rationale
Readability first (Phase 1) — it's the visible pain and feeds the README's screenshots. Performance
next (Phase 2) — its new numbers must land before docs quote them. Tests/research (Phase 3) harden
the base. Then the README overhaul (Phase 4) consumes the refreshed screenshots and measured
numbers. Links/consistency (Phase 5) and final validation (Phase 6) lock it.

---

## Status (2026-06-16) — execution log

- **Phase 1 — readability:** ✅ shipped. Render + HF muted contrast `#94A3B8→#B8C4D9`, legible
  disclaimer/term, HF file-widget hardening. Pushed to both remotes.
- **Phase 2 — performance:** ✅ profiled (`experiments/profile_pipeline.py`); BM25 text processing
  dominates, already cached+parallel+precompiled; honest verdict = no safe byte-identical speedup;
  documented in `performance_audit.md`.
- **Phase 3 — route tests:** ✅ all 13 FastAPI routes covered; closed the `/api/healthz` gap.
- **Phase 4 — README:** ✅ TOC, 2 mermaid diagrams (architecture + decision/validation), Live-demos
  section (HF + Render links, demo-video slot), embedded screenshots, full per-source results data +
  runtime matrix. Screenshots are interim (refresh after redeploy).
- **Phase 5 — links:** ✅ all internal links/images resolve; HF + Render live (200); study linked.
- **Phase 6 — validation:** ✅ 198 tests, reproduce.sh green, submission byte-stable each pass.

**Open (user actions / future):** make the GitHub repo public (currently 404 to anonymous);
record + link the demo video; rotate the API key; refresh the embedded screenshots once the
contrast redeploys land; optional deeper `experiments/` research-ledger sweep.
