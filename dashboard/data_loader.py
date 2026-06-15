"""Safe, deterministic, read-only loaders for committed local artifacts.

Import-light (NO streamlit, NO production imports). Never invents placeholder values into
data presented as real: a missing artifact returns a clear unavailable-status object.
"""
from __future__ import annotations

import json
from pathlib import Path

# pandas is imported lazily inside load_csv_safe so this module (and integrity_cards, which
# imports it) stays importable for test collection even when pandas is not installed.


class Artifact:
    """(ok, data, message). `ok=False` => render 'Artifact unavailable' + the expected path."""
    __slots__ = ("ok", "data", "message", "path")

    def __init__(self, ok, data, message, path):
        self.ok, self.data, self.message, self.path = ok, data, message, str(path)

    def __bool__(self):
        return self.ok


def load_json_safe(path) -> Artifact:
    p = Path(path)
    if not p.exists():
        return Artifact(False, None, f"Artifact unavailable — expected at {p}", p)
    try:
        with open(p, encoding="utf-8") as f:
            return Artifact(True, json.load(f), "ok", p)
    except Exception as e:  # malformed file — surface, never fabricate
        return Artifact(False, None, f"Artifact unreadable ({e.__class__.__name__}) at {p}", p)


def load_csv_safe(path) -> Artifact:
    p = Path(path)
    if not p.exists():
        return Artifact(False, None, f"Artifact unavailable — expected at {p}", p)
    try:
        import pandas as pd  # lazy: only CSV loading needs pandas
        return Artifact(True, pd.read_csv(p), "ok", p)
    except Exception as e:
        return Artifact(False, None, f"Artifact unreadable ({e.__class__.__name__}) at {p}", p)


def validate_required_columns(df, columns) -> tuple[bool, list]:
    if df is None:
        return False, list(columns)
    missing = [c for c in columns if c not in df.columns]
    return (len(missing) == 0), missing
