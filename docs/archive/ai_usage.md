# AI Usage Declaration

AI tools used:

- Codex for architecture planning, code generation, documentation drafting, and test scaffolding.
- Claude Code (Anthropic) for a later engineering pass: profiling and parallelising the
  feature-scoring step for runtime margin, building the independent (non-circular)
  evaluation harness, adding the LLM-wrapper and junior-for-senior soft JD penalties,
  and improving reasoning variety. All changes were reviewed and verified against the
  test suite and the format validator.
- Claude/Kimi audit notes were used as design-review references and compared against the repo before implementation.
- Claude Code (Anthropic) for the competition-hardening pass (2026-06-10): golden-hash
  reproduction gates, Docker runtime matrix, compute_features hot-path optimization
  (verified byte-identical), shared eval harness, pre-registered behavioral-floor
  sensitivity sweep, honeypot audit with manual verification, ablation ladder, the
  JD compiler, and the grounded-reasoning upgrade. Every change was gated on the
  full test suite plus golden-output regression tests.

`scripts/llm_judge_labels.py` can optionally call a hosted LLM **for development-time
evaluation labels only**. It is never invoked by the ranking path.

No candidate ranking step calls hosted AI services. The ranker does not send candidate data to OpenAI, Anthropic, Gemini, Cohere, or any external model API during ranking.

**Scope of the originality declaration.** `code_is_original_work: true` in
`submission_metadata.yaml` means: no code copied from other entrants or from
proprietary sources, and no collusion. It does not mean "written without AI
assistance" — the assistants above were used as disclosed, with every change
reviewed by the author and gated on the test suite, the golden-output
regression tests, and the format validator.
