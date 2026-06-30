# Frontend Polish Report

What was actually done, verified, and explicitly *not* done in the judge-facing frontend
pass. Nothing here is aspirational — every "verified" line was run in this environment.

## Golden safety

- **Golden hash before:** `af8f2b327f05d30e…`
- **Golden hash after:** `af8f2b327f05d30e…` — **byte-identical.**
- No production file (`rank.py`, `src/redrob_ranker/*`, weights, `submission.csv`) was touched.
  Production still does not import streamlit/gradio/dashboard. Firewall tests pass.

## Local dashboard — live render (verified)

- `pip install -r requirements-dashboard.txt` → streamlit 1.58.0 installed.
- `streamlit run omega_decision_dashboard.py --server.headless true` → `/_stcore/health`
  returned **200**, index returned **200**, no traceback in the server log.
- Executed end-to-end with Streamlit's supported **`AppTest`** harness: **0 exceptions**,
  **10 headers** rendered, 3 dataframes, and the Ψ panel still shows the
  **AWAITING HUMAN DATA** banner (honesty preserved).

## Changes made

1. **Drift fixed (single source of truth).** The dashboard previously hardcoded
   "171 passed". It now reads `tests_passing` from `docs/metrics_manifest.json` at runtime,
   so the count can never drift again. `dashboard/constants.py` gained `SHARED_FACTS` (verdict,
   golden commit, honeypot distinction, Ψ status) used by the dashboard and the parity tests.
2. **Deprecation fixed.** `use_container_width=True` (Streamlit removal date 2025-12-31, now
   passed) → `width="stretch"` in all 3 dataframes.
3. **Judge quick-nav** caption added above the fold listing the 9 numbered sections.
4. **HF Space synced.** `hf_space/app.py` and `hf_space/README.md` test-count badges
   corrected 171 → **198** to match the manifest. Hero KPIs (`0 / 53` honeypots, `80–125s`,
   `dev-proxy P@10`) already matched the manifest and were left intact.

## Tests added (CI guards)

- `tests/test_dashboard_smoke.py` (4 tests) — live `AppTest` render guard: runs without
  exception, renders all judge sections, keeps the AWAITING-HUMAN-DATA banner, and does not
  alter the golden hash. Collection-safe via `importorskip("streamlit")`.
- `tests/test_frontend_parity.py` (7 tests) — local dashboard ↔ HF Space cannot drift: test
  count tracks the manifest, verdict is consistent, canonical disclaimers present, HF README
  `sdk:` matches the imported framework, honeypot distinction matches the manifest, and the HF
  app makes no "confirmed fraud / official honeypot" claims. HF-touching tests `skipif` the
  submodule is absent (CI uses `submodules: false`), matching the existing hero test.
- Suite: **187 → 198 passed, 0 skipped** (local, hf_space present). Manifest + README badge
  updated together (anti-drift gate green).

## CI

- `.github/workflows/ci.yml` already installs `requirements-dashboard.txt`, so the new
  `AppTest` smoke test runs in CI with streamlit present.

## HF Space — local render (verified)

- `hf_space/app.py` imports and builds its Gradio `Blocks` graph without exception
  (gradio 6.10 local); the bundled `demo_sample.jsonl` exists and the auto-demo runs the
  **real** deterministic ranker on launch (confirmed by the captured screenshot showing a live
  ranked table + per-candidate fit breakdown).
- Launched headless on a local port; `GET /` returned **200**.

## Responsive / accessibility (measured with Playwright/Chromium)

Horizontal overflow (`scrollWidth − clientWidth`), measured live:

| Viewport | Streamlit dashboard | Gradio HF Space |
|---|---|---|
| 1440px desktop | 0px ✅ | 0px ✅ |
| 1024px laptop | 0px ✅ | 0px ✅ |
| 768px tablet | 0px ✅ | 0px ✅ |
| 390px mobile | 0px ✅ | 110px ⚠ (was 123px) |

- **Dashboard: zero overflow at every viewport.** Headings present; 0 `<img>` missing alt.
- **HF Space mobile residual (110px):** improved from 123px by lowering column `min_width`
  (420→320, 260→200, 320→260) and adding a `@media (max-width:480px)` rule that collapses the
  KPI/metric grids. The remaining overflow is the Gradio **Dataframe's intrinsic minimum
  width** (a 5-column ranked table will not shrink below ~500px), which Gradio controls; it is
  a horizontal scroll on phones only. Desktop/laptop/tablet — the judge-relevant sizes — are
  clean. Documented rather than hidden with `overflow-x:hidden` (which would clip content).
- Accessibility: 4 HF images all carry alt text; logical heading levels on both surfaces.

## Screenshots (real, captured this session)

Captured with Playwright/Chromium against the live local servers (not mockups):

- `docs/assets/dashboard-overview.png` — verdict banner, manifest-driven "198 passed" metric,
  judge quick-nav, shipping-gate battery.
- `docs/assets/dashboard-integrity-review.png` — 52-anomaly reconciliation + integrity cards.
- `docs/assets/dashboard-mobile.png` — 390px dashboard (no overflow).
- `docs/assets/huggingface-space.png` — live ranked table, KPI strip, candidate detail card.
- `docs/assets/huggingface-space-mobile.png` — 390px HF Space.

## Explicitly NOT done (honest)

- **No first-hand 50-competitor frontend audit** — no competitor clones available (see
  `FRONTEND_COMPETITIVE_AUDIT.md` for scope).
- **HF Space remote build not verified.** `hf_space` is a submodule pointing at the external
  Space `huggingface.co/spaces/bansal1234/Hirefit`. The local files are corrected, the app
  renders locally, and tests pass — but pushing to HF and watching its remote build requires
  the user's HF credentials and a deploy action. The fix is preserved as a local submodule
  commit; per the standing rule I do not claim a remote build is green.
- **HF Space 390px residual overflow (110px)** — Gradio Dataframe min-width limitation; see above.
- **No deep design-token system / candidate-comparison rebuild.** Targeted, low-risk polish
  only; the larger redesign remains a follow-up.

## Net

Both judge-facing surfaces now tell one consistent, manifest-backed story; the local
dashboard is verified to render live and is guarded by a CI smoke test; and the frozen golden
ranking remains byte-identical.
