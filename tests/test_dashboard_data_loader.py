"""Dashboard data-loading is safe, deterministic, and never fabricates values."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.data_loader import load_csv_safe, load_json_safe, validate_required_columns  # noqa: E402
from dashboard.constants import CONFIG  # noqa: E402


def test_missing_json_does_not_crash_and_flags_unavailable():
    art = load_json_safe(ROOT / "does" / "not" / "exist.json")
    assert art.ok is False and art.data is None and "unavailable" in art.message.lower()


def test_missing_csv_does_not_crash():
    art = load_csv_safe(ROOT / "nope.csv")
    assert art.ok is False and art.data is None


def test_real_artifacts_load():
    for key in ("registry", "omega_decision", "omega_frontier", "integrity_cards"):
        art = load_json_safe(CONFIG[key])
        assert art.ok, f"{key} should load from committed artifacts: {art.message}"


def test_deterministic_load():
    a = load_json_safe(CONFIG["omega_decision"])
    b = load_json_safe(CONFIG["omega_decision"])
    assert a.data == b.data


def test_validate_required_columns():
    art = load_csv_safe(CONFIG["phi_corpus"])
    if art.ok:
        ok, missing = validate_required_columns(art.data, ["evidence_status", "hiring_action"])
        assert ok, f"missing {missing}"
    ok2, missing2 = validate_required_columns(None, ["x"])
    assert ok2 is False and missing2 == ["x"]
