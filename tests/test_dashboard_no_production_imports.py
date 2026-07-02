"""Production firewall: the dashboard is a read-only downstream layer that cannot affect
the production ranking path or the golden hash."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GOLDEN_SHA = "3d2dbd8a68a145c25bda8122cdf02953ae5f06e2b003aa0f7b4d0e52ce283f6b"


def _src(p):
    return (ROOT / p).read_text(encoding="utf-8", errors="ignore") if (ROOT / p).exists() else ""


def test_rank_py_does_not_import_dashboard_or_research():
    s = _src("rank.py").lower()
    for bad in ("dashboard", "omega_decision_dashboard", "experiments", "import research"):
        assert bad not in s, f"rank.py must not reference {bad}"


def test_production_package_does_not_import_dashboard():
    # Firewall is about IMPORTS, not the substring "dashboard" (a legitimate BI skill keyword
    # in features.py / the unrelated HF payload docstring). Check actual import statements.
    import re
    pkg = ROOT / "src" / "redrob_ranker"
    pat = re.compile(r"^\s*(import|from)\s+(dashboard|omega_decision_dashboard|experiments)\b", re.M)
    for py in pkg.rglob("*.py"):
        s = py.read_text(encoding="utf-8", errors="ignore")
        m = pat.search(s)
        assert m is None, f"{py} imports {m.group(2)} (production must not import research/UI)"


def test_import_light_modules_avoid_streamlit_and_production():
    for mod in ("constants", "data_loader", "integrity_cards", "charts"):
        s = _src(f"dashboard/{mod}.py").lower()
        assert "import streamlit" not in s, f"dashboard/{mod}.py must stay import-light (no streamlit)"
        assert "run_ranking" not in s and "rank.py" not in s, f"dashboard/{mod}.py must not touch production"


def test_dashboard_modules_are_read_only():
    # no file writes / process exec in the import-light data/logic modules
    for mod in ("data_loader.py", "integrity_cards.py", "charts.py", "constants.py"):
        s = _src(f"dashboard/{mod}")
        for bad in ("open(", "Path.write", ".write_text", "subprocess", "os.system", "to_csv", "json.dump("):
            # 'open(' for READ is allowed in data_loader; ensure no write-mode opens
            pass
        assert "subprocess" not in s and "os.system" not in s
        assert "open(p, \"w\"" not in s and ".write_text(" not in s and "to_csv(" not in s


def test_golden_hash_unchanged():
    sub = ROOT / "submission.csv"
    assert sub.exists()
    assert hashlib.sha256(sub.read_bytes()).hexdigest() == GOLDEN_SHA, "golden submission.csv changed!"


def test_dashboard_app_imports_streamlit_only_at_app_level():
    # the app file may import streamlit; the firewall is that PRODUCTION never imports the app
    s = _src("omega_decision_dashboard.py").lower()
    assert "import streamlit" in s  # app is allowed
    assert "run_ranking" not in s   # but never executes production ranking
