# Dashboard Guide

`omega_decision_dashboard.py` — judge-facing 30–60s walkthrough of the Golden → Fusion → Ω →
Ψ → Φ arc. **Downstream explanation layer only**: reads committed local artifacts, never runs
or imports the production ranker; golden `af8f2b32` byte-identical.

## Run
```bash
pip install streamlit pandas         # streamlit is NOT a production dependency
streamlit run omega_decision_dashboard.py
```
(Streamlit is not installed in the production/test environment by design — the import-light
data/logic modules in `dashboard/` are unit-tested without it.)

## Sections
1 verdict banner · 2 shipping gates · 3 minimax-regret frontier (λ slider) · 4 the 52-anomaly
reconciliation + filterable table · 5 candidate audit card · 6 fusion autopsy · 7 Ψ status ·
8 Φ findings · 9 research timeline · 10 why golden ships.

## Data sources (all committed, read-only)
`experiments/registry.json`, `experiments/omega_outputs/*.json`,
`docs/human_opinion/integrity_cards.json`, `docs/human_opinion/corpus_phi2*.{csv,json}`,
`experiments/psi_panel/manifest.json`. Missing artifacts render "Artifact unavailable" with the
expected path — never invented values.

## Modules
`dashboard/constants.py` (paths, terms, mapping, gates) · `data_loader.py` (safe loaders) ·
`integrity_cards.py` (two-axis mapping) · `charts.py` (chart frames) · `components.py` (st render).
The first four are import-light (no streamlit) and tested in `tests/test_dashboard_*`.
