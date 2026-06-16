# Readability Audit — frontend low-contrast fixes (2026-06-16)

Triggered by two HF Space screenshots flagging hard-to-read text. Each problem is mapped to the
exact CSS fix in `hf_space/app.py` (and the shared token fix mirrored in `apps/api/static/index.html`).
Contrast measured on the `#0F172A` background.

## Screenshot 1 — `Screenshot 2026-06-16 184927.png` (upload / search / filter / disclaimer)

| Element | Problem (before) | Fix |
|---|---|---|
| Disclaimer paragraph | gray `#94A3B8`, faint at .74rem | `.disclaim` → `--text-secondary` (#CBD5E1, 12:1), .82rem |
| *"detector-flagged anomaly"* | faint italic, near-invisible | `.disclaim em` → `--text-primary` + dotted underline (no longer dimmer) |
| Upload label "Candidates (.jsonl…)" | mint-on-light-dropzone | `#upfile` id: dropzone forced `--bg-card`, label `--text-secondary`/600 |
| "Search" / "Filter" labels | faint mint | `label`/`fieldset legend` → `--text-secondary` |
| "Open to work" radio text | dim | label rules → secondary |
| KPI / metric sub-labels | muted `#94A3B8` (6.96:1) | token raised to `#B8C4D9` (**10.15:1**) globally |

## Screenshot 2 — `Screenshot 2026-06-16 184937.png` (run summary / download / footer)

| Element | Problem (before) | Fix |
|---|---|---|
| "Download full ranked CSV" button | teal-on-mint, very low contrast | `#dlfile` id: dark `--bg-card` bg, label `--text-secondary`/600, link `--accent` |
| Bottom footer ("Live execution · … · GitHub repository") | very faint gray, barely readable | `#appfoot` id: `--text-secondary` + `opacity:1` + .82rem; link → `--accent` |
| RUN SUMMARY / table / chips | already readable | unchanged |

## Method note

The global token bump (`--text-muted #94A3B8 → #B8C4D9`) lifts every muted label at once; the two
spots Gradio styles with its own low-contrast defaults (the file widgets and the markdown footer)
are pinned with **`elem_id`-targeted CSS**, which overrides Gradio's defaults reliably across
versions. Render mirrors the token + disclaimer fixes in `apps/api/static/index.html`.

**Verification:** the live HF Space and Render app rebuild on push; the embedded README screenshots
in `docs/assets/` are the pre-fix captures and should be refreshed once the rebuilds land.

## Second batch — `200454.png`, `200502.png`, `200508.png` (functional + contrast)

| Screenshot | Problem | Fix (`hf_space/app.py`) |
|---|---|---|
| 200454 | "Search" / "Filter" labels + radio options ("Open to work", "India", "Clean") faint | `elem_id` `searchbox`/`filterradio` + CSS forcing labels `--text-secondary` and option text `--text-primary` |
| 200502 | status line numbers ("60", "130 ms", …) invisible — markdown `**n**` → `<strong>` rendered dark | `status` `elem_id="rankstatus"`; CSS `#rankstatus strong → --accent` (numbers now pop) |
| 200508 | **empty download box** where the CSV download should be — `gr.File` output rendered as an empty dropzone | swapped to **`gr.DownloadButton`** (always a visible filled accent button); verified `postprocess(path) → FileData` so the download works |

Build-validated (Blocks construct, `DownloadButton.postprocess` returns valid `FileData` on the demo path). Pushed to HF; the live Space rebuilds.
