"""Live-render smoke test for the judge-facing dashboard.

Uses Streamlit's supported AppTest harness to actually EXECUTE
omega_decision_dashboard.py end-to-end (not just import it) and assert it renders
without throwing. This is the CI guard that the dashboard still runs after edits.

Collection-safe: if streamlit is not installed the whole module skips cleanly
(importorskip at import time), so the core suite still collects without dashboard deps.
"""
import hashlib
import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit", reason="dashboard presentation dep; install requirements-dashboard.txt")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
APP = ROOT / "omega_decision_dashboard.py"
GOLDEN_SHA = "c28857fdba63723ed13bea35d977a49f3aca7550dc7ea1c2c82d4150279e769c"


def _run():
    return AppTest.from_file(str(APP), default_timeout=90).run()


def test_dashboard_runs_without_exception():
    at = _run()
    assert not at.exception, f"dashboard raised: {list(at.exception)}"


def test_dashboard_renders_all_judge_sections():
    at = _run()
    # 9 numbered judge sections are emitted as st.header(...) (verdict is the title).
    assert len(list(at.header)) >= 9, "expected the full judge-journey section set"


def test_dashboard_keeps_awaiting_human_data_visible():
    # Honesty guard: the Ψ panel must still surface AWAITING HUMAN DATA, never a fabricated result.
    at = _run()
    assert any("AWAITING HUMAN DATA" in e.value for e in at.error), \
        "Ψ panel must show the AWAITING HUMAN DATA banner"


def test_dashboard_render_does_not_touch_golden():
    at = _run()
    assert not at.exception
    sub = ROOT / "submission.csv"
    assert hashlib.sha256(sub.read_bytes()).hexdigest() == GOLDEN_SHA, \
        "rendering the dashboard must never alter the golden submission"
