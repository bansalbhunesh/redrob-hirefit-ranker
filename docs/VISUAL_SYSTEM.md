# HireFit visual system

HireFit presents ranking as a **forensic decision room**: the shortlist is a conclusion, and every
conclusion must expose the evidence that produced it. This direction is deliberately different from
generic dark-glass AI dashboards. It combines an editorial casefile with a working recruiter ledger.

## Experience architecture

1. **Rankings** starts with the active search and moves directly into the populated candidate ledger.
2. **Method** progressively discloses retrieval, evidence verification, integrity gating, and stable ranking.
3. **Validation** exposes the artifact hash, test receipt, runtime, compute budget, and shortlist gate.

The first screen communicates the decision. Deeper methodology is available on request rather than
competing with the primary task.

## Shared presentation language

- Mineral neutrals replace the common cream-template palette.
- Rust identifies decisions and active controls; green is reserved for verified status.
- Literata carries the editorial casefile voice, Manrope carries product UI, and Azeret Mono is limited
  to hashes, receipts, and machine-readable facts.
- Translucency is reserved for navigation and major foreground surfaces. Dense evidence remains opaque
  enough to read quickly.
- Day and night files preserve the same hierarchy instead of becoming separate designs.

## Interaction rules

- Selected filters use a filled state, border, and `aria-pressed` or native checked state.
- Method layers use native `details` disclosure and remain keyboard operable.
- Candidate cards support pointer, Enter, and Space activation.
- Motion communicates entrance and state change using opacity and transforms only.
- `prefers-reduced-motion` removes nonessential motion.
- Controls are at least 44px high in the primary workflows; focus indicators remain visible against
  both presentation modes.

## Responsive behavior

- Navigation wraps before it collides with mode controls.
- The ranking summary becomes a two-column phone grid.
- Filters become a two-column control matrix with search spanning the full width.
- The evidence dossier leaves the desktop sticky rail and enters normal document flow on narrow screens.
- Method and validation panels collapse to one column without hiding functionality.

## Quality gates

- `npx impeccable --json apps/api/static/index.html`: zero findings.
- Current full local suite: 278 passed.
- Frozen `submission.csv` SHA-256 remains
  `3d2dbd8a68a145c25bda8122cdf02953ae5f06e2b003aa0f7b4d0e52ce283f6b`.
- Public Render `/api/readyz` reports the merged Git SHA and loaded dashboard.
- Public HF navigation, progressive disclosure, filter selection, and zero horizontal desktop overflow
  are browser-verified after deployment.

## Research basis

- Nielsen Norman Group: progressive disclosure should keep common actions visible and reveal specialized
  detail only when requested.
- Apple Human Interface Guidelines: materials should create hierarchy between foreground controls and
  content, not become decoration everywhere.
- WCAG 2.2: focus appearance and target sizing must make state and interaction discoverable.
- web.dev: avoid layout-property animation and layout thrashing to protect interaction latency.
