# Frontend Unified Audit & Design System

> **Update (2026-06-16, later):** the teal "Decision Instrument" system below was **superseded
> by "Command Core"** — a mission-control aesthetic: **indigo `#4F46E5`** (no teal), **Inter +
> JetBrains Mono**, sharp edges (≤2px), hairline borders, no shadows, monospace numerals. It is
> now applied across **all three** surfaces (Omega Streamlit dashboard, Render frontend, HF
> Space). Tokens live in `dashboard/theme.py`. The audit findings below still hold; only the
> palette/type direction changed.

Brutally honest review of the two judge-facing surfaces, 2026-06-16.

- **Render frontend** = `apps/api/static/index.html` (self-contained dark SPA "Redrob HireFit
  Ranker v3.0", served by `apps/api/main.py`).
- **HF Space** = `hf_space/app.py` (Gradio, light theme, "HireFit Ranker").

**Scope honesty:** I do **not** have the 50 competitor frontends checked out, so I cannot
score this against them pixel-for-pixel. Claims below compare the two apps to each other and to
general senior-review standards, not to a fabricated competitor matrix.

## Verdict in one line

Both are individually competent, but they read as **two different products** (dark vs white,
two wordmarks, two KPI sets, two type treatments) and the Render app carries a **factual error
(28-D)** and **un-disclaimed "honeypots blocked" bravado** that contradicts the rigorous
disclaimers everywhere else in the submission — the single biggest judge-perception risk.

## Ranked problems

| # | Sev | Where | Problem | Why it harms a judge | Exact fix |
|---|-----|-------|---------|----------------------|-----------|
| 1 | **CRIT** | Render KPI + filter (022520) | "53 **HONEYPOTS BLOCKED**" + red "Honeypots" filter, **no disclaimer** | Directly contradicts the project's own canon (*detector-flagged anomaly ≠ confirmed fraud ≠ official planted honeypot*) and the HF/dashboard disclaimers; a judge who reads the docs sees the team overclaiming | Relabel "Integrity screen · 53 flagged, 0 in shortlist"; add footnote disclaimer; rename filter "Integrity-flagged" |
| 2 | **CRIT** | Render header vs HF hero | Two wordmarks: "Redrob HireFit Ranker v3.0" vs "HireFit Ranker" | Reads as two separate teams/products; erodes trust | One wordmark "Redrob HireFit Ranker" + shared tagline on both |
| 3 | **CRIT** | whole-page theme | Render full dark navy; HF white page | Strongest "different product" signal | One dark system on both (HF via CSS) |
| 4 | **HIGH** | Render pipeline (022520) | "**28-D Features**" — production has **33** (`FEATURE_NAMES`=33; HF correctly says 33) | Factual inconsistency a technical judge will catch | "33 Features" |
| 5 | **HIGH** | Render table (022454/022507) | "Why" reasoning column header truncates to "My…"; reasoning is an unreadable wall of 8px text | Core value (grounded reasoning) looks broken/illegible | Rename header "Reasoning"; clamp to 2 lines + ellipsis; move full text to the detail panel |
| 6 | **HIGH** | Render empty states (022551) | 🔍 emoji "No candidates match" + a stray face/💗 emoji bottom-right | Emojis read as unfinished/accidental on a "premium" tool | Replace with inline SVG + tokens; remove stray emoji widget |
| 7 | **HIGH** | both | Two KPI sets w/ different scales (Render "AVG SCORE 0.722" vs HF "Avg fit score 0.197") | Same product reporting different numbers confuses | Shared KPI definitions + labels |
| 8 | **MED** | Render above-fold (022520) | Giant empty uploader dominates; results sit below the fold; right panel is a large "No candidate selected" void on load | Judge's first screen is empty chrome, not proof | Auto-load the demo result; compress uploader to a slim bar once data exists |
| 9 | **MED** | both | Body font = **Inter** (generic); numerals not tabular everywhere | Generic "AI-slop" type; misaligned numeric columns | Distinctive type system (below) |
| 10 | **MED** | Render | Muted text `#475569`/`#64748b` on `#090b11` for real labels | Borderline WCAG contrast | Lift muted to `#8b97a8`+ for labels |
| 11 | **MED** | Render pipeline | 8-box stepper repeats "100,000" ×5 | Visual crowding, low info gain | Condense to a single inline flow with counts only where they change |
| 12 | **MED** | HF (390px) | 110px horizontal overflow on mobile | Mobile judges get a side-scroll | Documented Gradio Dataframe min-width limit; mitigated |
| 13 | LOW | Render header | "v3.0" badge | Version vanity, no judge value | Drop or demote |

## Unified design system ("Decision Instrument")

One dark, high-trust, data-forward identity on **both** surfaces.

**Identity**
- Wordmark: **Redrob HireFit Ranker** · tagline *"Ranks careers, not keywords."*
- Logo mark: square `R`, teal hairline border.

**Color tokens (canonical — already the Render `:root`, now shared with HF)**
```
--bg-deep:#090b11  --bg-panel:#111420  --bg-card:#151926  --border:rgba(255,255,255,.07)
--text-primary:#f4f7fb  --text-secondary:#9fb0c3  --text-muted:#8b97a8   (lifted for contrast)
--accent:#14b8a6 (teal, primary)  --success:#10b981  --warning:#fbbf24  --danger:#ef4444
```
Dominant near-black + a single teal accent; amber/red only for status. No purple gradients.

**Typography (replaces Inter)**
- Display / wordmark / headings: **Bricolage Grotesque** (characterful, editorial).
- Body / UI: **IBM Plex Sans** (refined, technical, high-trust).
- Numerals / scores / code: **IBM Plex Mono**, `font-variant-numeric: tabular-nums`.

**Status semantics (color + label + icon, never color-only)**
- Shipped integrity screen → neutral shield, label "flagged for review", never "blocked/fraud".
- Any integrity annotation uses the locked canon Evidence{CLEAR/AMBIGUOUS/PROBABLE/CONFIRMED}
  × Action{CONTINUE/CLARIFY/VERIFY/DOWNRANK/BLOCK} from the dashboard.

**Terminology canon (locked across both)**
- "33 features" · "shipped integrity screen flagged 53 · 0 in shortlist" · disclaimer
  *"detector-flagged ≠ confirmed fraud ≠ official planted honeypot"* · never bare "honeypots blocked".

**Disclaimers preserved:** dev-proxy label, "No official hidden labels", golden byte-identical,
NO_RANKING_DOMINATES — all retained verbatim.

## Implementation — what changed

**Shared (both surfaces):** one wordmark "Redrob HireFit Ranker" + "R" logo + tagline; one
type system (Bricolage Grotesque display / IBM Plex Sans body / IBM Plex Mono tabular
numerals) replacing Inter; one dark palette (`#090b11`/`#151926` + teal `#14b8a6`); one
terminology canon ("33 features", "Integrity-flagged", the detector-flagged-anomaly
disclaimer); dev-proxy / "no official hidden labels" / golden / NO_RANKING_DOMINATES kept.

**Render (`apps/api/static/index.html`):** fonts; "28-D"→"33 Features" (#4); "Honeypots
Blocked"→"Integrity-flagged" + disclaimer footnote (#1); filter + pipeline node relabelled;
🔍/stray emoji → inline SVG (#6); muted text lifted for contrast (#10); CSS-grid blowout fixed
→ **0px overflow at 390/768/1024/1440** (was 634px on mobile); "v3.0"→"LIVE · CPU-only".

**HF Space (`hf_space/app.py`):** full dark re-skin via CSS (forces dark regardless of system
theme), shared fonts/wordmark/logo/disclaimer, dark native widgets + table, KPI relabelled
"integrity-flagged · 0 in shortlist". 0px overflow desktop+mobile.

## Re-judgement (after implementation)

Scored the same matrix on the post-change builds (live local render, desktop+mobile):

| Dimension | Render before | Render after | HF before | HF after |
|---|--:|--:|--:|--:|
| Brand consistency (cross-app) | 2 | 5 | 2 | 5 |
| Typography | 3 | 4 | 3 | 4 |
| Scientific-honesty of labels | 2 | 5 | 4 | 5 |
| Visual quality | 4 | 4 | 3 | 4 |
| Responsiveness | 2 | 5 | 3 | 5 |
| Empty/error states | 3 | 4 | 4 | 4 |

The two apps now share wordmark, logo, palette, type, accent, and terminology, and both pass a
live 0-overflow desktop+mobile check — they read as **one product**. This is **not** claimed
"best of all 50 competitor frontends": no competitor frontend was inspected this round, so that
claim is unsupported and not made. What the before/after screenshots in `docs/assets/`
(`render-desktop/mobile`, `hf-desktop/mobile`) do support: a measurable jump in cross-app
coherence and label honesty, with the factual "28-D" error removed.

## Honest residuals

- HF native-widget dark overrides were verified on local **gradio 6.10**; the live Space runs
  **5.49.1** (different DOM) — core dark (body/container/inputs/table) uses version-robust
  selectors, but minor widget chrome may differ on the live build (re-verified post-deploy).
- No first-hand competitor-frontend inspection (no clones).
- HF candidate **table** can still side-scroll inside its own panel on very narrow phones
  (Gradio Dataframe min content width) — contained, not a page overflow.
