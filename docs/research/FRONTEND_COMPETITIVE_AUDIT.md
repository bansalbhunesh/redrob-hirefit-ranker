# Frontend Competitive Audit

**Scope honesty (read first).** This audit does **not** rest on a fresh inspection of 50
competitor *frontends*. No competitor frontend repositories are checked out in this
workspace, and cloning/serving dozens of third-party demos to capture pixel-level UX was not
performed. Presenting a 50-row per-repo score matrix here would be fabrication. Instead this
document:

1. records the **real** competitive evidence already established in this repo
   (`docs/COMPETITIVE_LANDSCAPE.md`, `docs/research/`, `competitor_validation_report.md`) and
   in the maintained competitor notes;
2. applies the requested **weighted evaluation matrix** to the surfaces we *can* characterize
   — our own two judge-facing surfaces and the rival patterns we have genuinely observed; and
3. names the frontend patterns worth adopting, with the ones we rejected and why.

Where a row is not from a first-hand re-inspection this session, it is marked
`(prior analysis)` or `(pattern, not re-inspected)`. Competitor repo names follow the
landscape doc's convention and are referenced only where prior analysis recorded them.

---

## Method

- **Our surfaces (first-hand, this session):** the local Streamlit dashboard
  (`omega_decision_dashboard.py`) was live-rendered headless (health 200) and executed
  end-to-end via Streamlit `AppTest` (0 exceptions, 10 sections). The HuggingFace Gradio
  Space (`hf_space/app.py`) was read in full and its facts cross-checked against
  `docs/metrics_manifest.json`.
- **Competitors:** drawn from prior validated analysis. The strongest documented rivals are a
  learned-reranker team (records the semantic lever we measured as empty) and a
  **dashboard-polish leader** ("Thermo"-class) whose only documented edge over us is
  presentation. None matched our validation rigor.

## Weighted evaluation matrix

| Dimension | Weight |
|---|--:|
| Judge time-to-understanding | 20% |
| Information architecture | 15% |
| Candidate exploration | 15% |
| Explanation clarity | 15% |
| Visual quality | 10% |
| Demo reliability | 10% |
| Responsiveness | 5% |
| Accessibility | 5% |
| Error/loading states | 5% |

### Scores (0–5; weighted total normalized to 100)

| Dimension | Our local dashboard | Our HF Space (Gradio) | Dashboard-polish rival *(prior analysis)* |
|---|--:|--:|--:|
| Judge time-to-understanding | 4 | 4 | 4 |
| Information architecture | 4 | 4 | 3 |
| Candidate exploration | 4 | 5 | 3 |
| Explanation clarity | 5 | 5 | 3 |
| Visual quality | 3 | 4 | 4 |
| Demo reliability | 5 | 4 | 3 |
| Responsiveness | 3 | 4 | 3 |
| Accessibility | 3 | 3 | 3 |
| Error/loading states | 5 | 4 | 3 |
| **Weighted total /100** | **81** | **85** | **67** |

These are **assessor scores by the maintainer**, not blind third-party judging. They are
defensible from observed behavior (e.g. our reliability is backed by an `AppTest` smoke run
and graceful artifact-unavailable states; the rival's visual edge is from prior notes). They
are not a claim of "best among all 50 teams" — only that against the evidence we hold, our
two surfaces lead on explanation clarity, candidate exploration, and demo reliability, and
trail the polish leader only on raw visual quality, which this polish pass narrows.

## Strongest patterns worth adopting

- **Live, inspectable candidate detail** (already in our HF Space): per-candidate fit
  breakdown bars + grounded reasoning + the guardrail penalty that actually fired. This is our
  biggest differentiator; keep and mirror its terminology in the dashboard.
- **A single hero KPI strip** answering "what / how fast / how safe" above the fold.
- **Search + filter chips** over the ranked table (we have this in both surfaces).

## Patterns rejected

- **Cyberpunk / heavy-gradient "AI" theming** common in hackathon demos — rejected; it
  undermines a high-trust recruiting-intelligence read.
- **Fake "fraud confirmed" / "honeypot caught" labels** seen in detection-bragging UIs —
  rejected as a hard honesty violation. We say *detector-flagged anomaly ≠ confirmed
  contradiction ≠ official planted honeypot* and never assert confirmed fraud.
- **Precomputed "live" demos** — rejected; our HF Space runs the real deterministic pipeline
  (capped pool) rather than replaying a fixed result.

## Honest gaps (not closed this session)

- No first-hand 50-repo frontend re-inspection (no competitor clones available).
- HF Space **remote** build not verified from here (submodule → external Space; needs HF creds).
- HF Space has a residual 390px-mobile horizontal scroll (Gradio Dataframe min-width).

Closed this session: real Playwright/Chromium screenshots of both surfaces, a measured
responsive overflow matrix, and a local HF render. See `FRONTEND_POLISH_REPORT.md`.
