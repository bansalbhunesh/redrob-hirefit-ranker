from __future__ import annotations

from scripts.jd_generalization_probe import probe


def test_probe_compiles_supported_technical_jds_and_refuses_sales_role():
    results = probe()

    assert results["senior_ai_engineer"]["status"] == "compiled"
    assert "llm_production" in results["senior_ai_engineer"]["must_groups"]
    assert "vector_database" in results["senior_ai_engineer"]["must_groups"]

    assert results["backend_platform_engineer"]["status"] == "compiled"
    assert "python_ml_engineering" in results["backend_platform_engineer"]["must_groups"]
    assert "distributed_systems" in results["backend_platform_engineer"]["nice_groups"]

    assert results["search_relevance_engineer"]["status"] == "compiled"
    assert "ranking_information_retrieval" in results["search_relevance_engineer"]["must_groups"]

    assert results["unsupported_sales_manager"]["status"] == "unsupported"
