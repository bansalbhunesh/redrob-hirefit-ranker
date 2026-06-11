from __future__ import annotations

import csv

from scripts.summarize_counterfactual_proxy_audit import summarize


def test_summary_counts_direction_and_percentiles(tmp_path):
    path = tmp_path / "audit.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["variant", "score_delta"])
        writer.writeheader()
        writer.writerows(
            [
                {"variant": "name_neutralized", "score_delta": "0.0"},
                {"variant": "name_neutralized", "score_delta": "0.0"},
                {"variant": "location_undisclosed", "score_delta": "-0.2"},
                {"variant": "location_undisclosed", "score_delta": "0.0"},
                {"variant": "location_undisclosed", "score_delta": "0.1"},
            ]
        )

    summary = summarize(path)

    assert summary["name_neutralized"]["n"] == 2
    assert summary["name_neutralized"]["nonzero"] == 0
    assert summary["location_undisclosed"]["n"] == 3
    assert summary["location_undisclosed"]["positive"] == 1
    assert summary["location_undisclosed"]["negative"] == 1
    assert summary["location_undisclosed"]["min"] == -0.2
    assert summary["location_undisclosed"]["max"] == 0.1
    assert summary["location_undisclosed"]["max_abs"] == 0.2
