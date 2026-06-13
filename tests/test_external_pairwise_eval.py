from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_external_pairwise_eval.py"
    spec = importlib.util.spec_from_file_location("run_external_pairwise_eval", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = _load_module()


def test_roc_auc_handles_perfect_tied_and_reversed_rankings():
    assert mod.roc_auc([0.9, 0.8, 0.1, 0.0], [1, 1, 0, 0]) == 1.0
    assert mod.roc_auc([0.5, 0.5], [1, 0]) == 0.5
    assert mod.roc_auc([0.1, 0.2, 0.9, 0.8], [1, 1, 0, 0]) == 0.0


def test_keyword_overlap_is_higher_for_matching_resume():
    jd = "Senior Software Engineer with Java, Spring Boot, REST APIs, SQL and AWS."
    good = "Software Engineer with 7 years Java Spring Boot REST API SQL AWS microservices."
    bad = "Retail sales manager with store operations and visual merchandising."

    assert mod.keyword_overlap(good, jd) > mod.keyword_overlap(bad, jd)


def test_pair_scorer_prefers_matching_technical_resume():
    jd = """
Senior Software Engineer, 5-8 years. Build Java Spring Boot REST APIs,
microservices, SQL-backed platforms and AWS services.
"""
    good_resume = """
Senior Software Engineer with 7 years of Java, Spring Boot, REST API and
microservices delivery. Built SQL-backed production services on AWS.
"""
    bad_resume = """
Marketing manager with 7 years in campaigns, event planning, retail sales and
brand communications. No software engineering delivery.
"""

    good = mod.score_pair("GOOD", good_resume, jd, "Good Fit")
    bad = mod.score_pair("BAD", bad_resume, jd, "No Fit")

    assert good is not None
    assert bad is not None
    assert good.hirefit_score > bad.hirefit_score


def test_downloader_rejects_non_http_urls(tmp_path):
    target = tmp_path / "dataset.csv"

    try:
        mod.download_if_missing(target, url="file:///tmp/not-a-dataset.csv")
    except ValueError as exc:
        assert "unsupported URL scheme" in str(exc)
    else:  # pragma: no cover - defensive clarity for failed guardrail
        raise AssertionError("download_if_missing accepted a non-http URL")
