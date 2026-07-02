from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# The script under test needs this dev-extra dep; without the guard a base
# `pip install -e .` environment dies with a collection error, not a skip.
pytest.importorskip("defusedxml", reason="dev extra dep; install '.[dev]'")

ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "research_public_data_leads.py"
    spec = importlib.util.spec_from_file_location("research_public_data_leads", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = _load_module()


def test_fetch_text_rejects_non_http_urls():
    status, body, error = mod.fetch_text("file:///tmp/not-a-public-page")

    assert status is None
    assert body == ""
    assert "unsupported URL scheme" in error
