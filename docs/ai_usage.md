# AI Usage Declaration

AI tools used:

- Codex for architecture planning, code generation, documentation drafting, and test scaffolding.
- Claude Code (Anthropic) for a later engineering pass: profiling and parallelising the
  feature-scoring step for runtime margin, building the independent (non-circular)
  evaluation harness, adding the LLM-wrapper and junior-for-senior soft JD penalties,
  and improving reasoning variety. All changes were reviewed and verified against the
  test suite and the format validator.
- Claude/Kimi audit notes were used as design-review references and compared against the repo before implementation.

`scripts/llm_judge_labels.py` can optionally call a hosted LLM **for development-time
evaluation labels only**. It is never invoked by the ranking path.

No candidate ranking step calls hosted AI services. The ranker does not send candidate data to OpenAI, Anthropic, Gemini, Cohere, or any external model API during ranking.
