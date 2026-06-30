# Code Audit & Polish — 2026-06-14

Whole-repo polish, deep audit, and exhaustive test pass. **The submission is frozen**
(golden `af8f2b32`, tag `v1.0-submission`); every change below is behavior-preserving and was
verified against the golden-hash regression (`tests/test_submission_gate.py`, which re-runs the
ranker on a 2k slice and matches `e4623c21…`). Submission output is byte-identical.

## Test suite — exhaustive

- **171 passed, 0 skipped** (was 165) in ~11s; full collection (httpx + defusedxml present).
- Golden-output regression green → ranking unchanged.
- **Coverage 91%** (was 87%), via `pytest-cov`. Ship-path modules:
  `jd_compiler.py` 100%, `constants.py` 100%, `integrity.py` 100%, `text.py` 100%,
  `pipeline.py` 97%, `features.py` 95%, `eval_harness.py` 95%, `reasoning.py` 94%.
- **New tests:** `tests/test_pessimistic_judge.py` (6) lifts `pessimistic_judge.py`
  **0% → 80%** — pure deterministic gate logic that was previously untested.
- Remaining low-coverage modules are all **off the submission path**: `eval.py` 34% (report
  helpers used only by scripts; the ship-critical `dcg` is exercised via `eval_harness`),
  `_cgroup.py` 58% (Linux container memory detection, not reachable on the test host),
  `pessimistic_judge.py` 80% (offline label tool).

## Lint — ruff 0.15.17

- **`src/`, `apps/`, `tests/` are clean (0 errors).**
- 28 issues auto-fixed (unused imports / empty f-strings) across src + non-src.
- Remaining lint lives only in `scripts/` and the `hf_space` submodule and is the intentional
  `sys.path.insert(...)`-then-import idiom (E402), research-script one-liners (E702), and short
  loop names (E741). Not suppressed, documented here — these are throwaway research utilities,
  not shipped ranking code.

## Behavior-preserving fixes applied

| Fix | Where | Note |
|---|---|---|
| Removed 5 dead local assignments | `features.py` | `signals`/`skills` in `_honeypot_flags`; `raw_github` (superseded by `github_signal`) — pure, unused |
| Removed 10 unused imports | `features.py`, `moe_scorer.py`, `pessimistic_judge.py`, `reasoning.py`, `retrieval.py` | F401 |
| `CompiledJD` forward-ref | `features.py` | added `TYPE_CHECKING` import; was an F821 (string annotation, no runtime effect) |
| Tightened a weak test | `test_reasoning.py` | `test_reasoning_mentions_only_real_skills` built `reasoning` but never inspected it — kept as an explicit smoke assertion |
| Non-src auto-fixes | `apps/api/main.py`, `tests/test_embeddings.py`, `scripts/*` | unused imports / empty f-strings |

## Latent design findings — SURFACED, not changed

Two product signals are computed in `features.py` and then discarded. They were removed as dead
code (net-zero on output), but the **intent** is recorded here because activating either is a
deliberate, golden-changing, blind-set-gated decision — not a silent fix:

1. **Management-track signal** — `_count_tokenized(_MANAGEMENT_SPLIT, tokens_career, safe_career)`
   detected manager-track language but fed nothing. Possible intent: down-weight people-manager
   profiles for this IC role. *Would change the golden hash; must pass the blind gate like any
   feature change (see `docs/measured_negatives.md`).*
2. **Off-target-title flag** — `_has_boundary(_NON_TARGET_PADDED, current_title)` flagged
   off-role current titles but fed nothing. Possible intent: a title penalty. *Same caveat.*

Given the ten measured negatives already on record (every feature/model lever tested has failed
the blind arbiter), neither is recommended without a passing blind-set gate.

## Posture confirmed

- **Determinism:** `PYTHONHASHSEED=0` + pinned BLAS threads; suite reproduces identically.
- **Security:** CVE-pinned `starlette`/`gradio`/`pillow` extras; `defusedxml` for XML; no bare
  `except:` in `src/`.
- **Verdict:** production ranking code is lint-clean, 91%-covered (95–100% on the ship path),
  and byte-identical to the frozen submission. No defects found on the submission path.
