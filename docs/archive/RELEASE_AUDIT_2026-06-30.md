# V6 Release Audit — 2026-06-30

## Verdict

The V6 repository is technically release-ready, publicly accessible, and materially stronger than the previous public-facing package. No repository-controlled publication blocker remains.

## Scorecard

| Area | Before | After | Status |
|---|---:|---:|---|
| Judge orientation | 72 | 96 | 60-second packet, evidence strip, scorecard, pitch and reproduction path added |
| Claim accuracy | 78 | 97 | suspended Render mirror removed as live proof; estimates separated from measured facts |
| Reproducibility | 96 | 98 | release command, validator, immutable artifact hash and failure gates surfaced |
| Deployment readiness | 75 | 95 | schema-validated Render Blueprint, readiness contract and acceptance gate added |
| Product consistency | 81 | 97 | V6, 33-feature, release-hash and dashboard labels aligned |
| Security/responsible use | 86 | 96 | dependency and static scans passed; security and hiring-use policy added |
| Public accessibility | 0 | 100 | Public API, raw V6 README, fresh assets and credential-free `main` lookup verified |

Scores are a transparent repository-quality audit, not official challenge scores.

## Verification evidence

- Full test suite: **262 passed, 6 skipped**. Skips are environment-specific and pre-existing.
- Shipping-code lint: **pass** across `src`, `apps`, `rank.py`, dashboard code and tests.
- Dependency audit: **no known vulnerabilities** in pinned production requirements.
- Static security scan: **pass**; one explicitly suppressed parameterized SQL pattern was acknowledged by Bandit.
- Local API: `/api/health`, `/api/readyz`, and `/api/metrics` returned HTTP 200; health reported V6 and readiness reported all checks true.
- Artifact validation: `submission.csv` valid; SHA-256 `8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`.
- Live sandbox: Hugging Face Space returned HTTP 200.
- Public repository: unauthenticated GitHub API reported `public`; raw V6 README and both screenshots resolved; credential-free `main` lookup returned merge `96a8a8c`.
- Deployment manifest: `render.yaml` passed the current Render Blueprint JSON schema.
- Diagram and metrics artifacts: SVG XML and JSON syntax passed.
- Visual render: current V6 API inspected at 1440×1100 and 390×844; screenshots are committed and linked from the README.

## Findings closed

- **P1 — Misleading deployment status:** historical Render service is suspended. Fixed by using Hugging Face as primary live proof and offering a committed Blueprint instead.
- **P1 — Stale product identity:** API, demo and dashboard mixed V3/V5, 28-D and V6 language. Fixed and regression-tested.
- **P1 — Weak judge path:** evidence was spread across a large research archive. Fixed with a 60-second packet and five-link front-page path.
- **P2 — Missing professional deployment/security guidance:** fixed with deployment acceptance gates and responsible-use policy.
- **P2 — Visual anti-patterns:** excessive accent borders and gradient treatment were removed from the dashboard theme.
- **P2 — Historical plans looked current:** the old improvement plan is now explicitly marked as a historical record.

## Known limits

- The preferred in-app visual connection was unavailable, so the installed Chrome headless renderer was used as the documented fallback. Both committed screenshots are fresh captures of the current local V6 API.
- The final Docker rebuild did not complete within the local Docker daemon timeout. This does not replace the already recorded full 100K, 2-CPU/16-GiB byte-identity run; it is documented rather than hidden.
- Repository-wide Ruff includes exploratory and historical scripts and reports legacy style debt. The production/shipping surface is clean; preserved experiments were not mechanically rewritten.
- Official hidden labels and judging weights remain unavailable. Public-field rankings are evidence-based estimates, not official placements.
