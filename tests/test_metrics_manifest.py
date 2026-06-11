"""Anti-drift gate: every KPI surface must agree with docs/metrics_manifest.json.

The manifest is the single source of truth for numbers quoted in the README,
the API showpiece payload, and the HF Space hero. A number changed in one
surface but not the manifest (or vice versa) fails here — no more 80s in one
place and 104s in another.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "docs" / "metrics_manifest.json").read_text(encoding="utf-8"))
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_tests_badge_matches_manifest():
    expected = MANIFEST["tests_passing"]
    assert f"tests-{expected}_passing" in README, (
        f"README tests badge does not say {expected}; update the badge and the "
        "manifest together."
    )


def test_manifest_tests_count_matches_collected_suite():
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    match = re.search(r"(\d+) tests? collected", completed.stdout)
    assert match, f"could not parse collected count from:\n{completed.stdout[-2000:]}"
    collected = int(match.group(1))
    assert collected == MANIFEST["tests_passing"], (
        f"Suite collects {collected} tests but manifest/README say "
        f"{MANIFEST['tests_passing']}. Update docs/metrics_manifest.json and the "
        "README badge."
    )


def test_readme_dev_proxy_metrics_match_manifest():
    ev = MANIFEST["dev_proxy_eval"]
    assert f"NDCG@10 {ev['ndcg10']:.4f}" in README
    assert f"P@10 = {ev['p10']:.1f}" in README
    # The qualifier must be in the headline metrics area, not buried in docs.
    assert "dev proxy" in README.lower()
    assert "No official hidden labels" in README


def test_readme_runtime_claims_are_manifest_values():
    rt = MANIFEST["runtime"]
    assert f"{rt['cloud_2vcpu_serial_s']}s" in README
    rounded_local = round(rt["local_docker_serial_best_s"])
    assert f"{rounded_local}s" in README, (
        f"README should quote ~{rounded_local}s for the local Docker serial run "
        f"(manifest: {rt['local_docker_serial_best_s']} s)"
    )


def test_precomputed_payload_matches_manifest():
    payload = json.loads(
        (ROOT / "apps" / "api" / "data" / "precomputed.json").read_text(encoding="utf-8")
    )
    meta = payload["metadata"]
    sub = MANIFEST["submission"]
    assert meta["total_candidates"] == sub["total_candidates"]
    assert meta["ranked_count"] == sub["rows"]
    assert meta["honeypots_blocked"] == sub["honeypots_detected"]
    assert meta["honeypots_in_output"] == sub["honeypots_in_top100"]
    assert meta["avg_score"] == sub["avg_top100_score"]
    assert meta["processing_time_ms"] == MANIFEST["runtime"]["showpiece_recorded_run_ms"]
    assert meta["bm25_backend"] == MANIFEST["bm25_backend"]


def test_hf_space_hero_matches_manifest():
    app = (ROOT / "hf_space" / "app.py").read_text(encoding="utf-8")
    sub = MANIFEST["submission"]
    assert f"{sub['honeypots_in_top100']} / {sub['honeypots_detected']}" in app
    rt = MANIFEST["runtime"]
    rounded_local = round(rt["local_docker_serial_best_s"])
    assert f"{rt['cloud_2vcpu_serial_s']}" in app and f"{rounded_local}" in app, (
        "HF Space hero runtime KPI must quote manifest values "
        f"({rt['cloud_2vcpu_serial_s']} s cloud / ~{rounded_local} s Docker), "
        "not an untraceable number."
    )
    assert "dev-proxy" in app, "HF Space P@10 KPI must carry the dev-proxy label"


def test_golden_hash_matches_submission_gate():
    gate = (ROOT / "tests" / "test_submission_gate.py").read_text(encoding="utf-8")
    match = re.search(r'GOLDEN_SUBMISSION_SHA256 = "([0-9a-f]{64})"', gate)
    assert match
    assert match.group(1) == MANIFEST["submission"]["golden_sha256"]
