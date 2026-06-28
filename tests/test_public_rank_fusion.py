from __future__ import annotations

import pytest

from experiments.public_rank_fusion import weighted_rrf


def test_weighted_rrf_preserves_locked_prefix_and_uniqueness() -> None:
    base = ["a", "b", "c", "d"]
    other = ["d", "c", "x", "a"]

    fused = weighted_rrf(base, [(other, 3.0)], lock=2, rrf_k=1)

    assert fused[:2] == ["a", "b"]
    assert len(fused) == len(set(fused)) == 4
    assert "d" in fused


def test_weighted_rrf_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="lock"):
        weighted_rrf(["a"], [], lock=2)
    with pytest.raises(ValueError, match="non-negative"):
        weighted_rrf(["a"], [(["b"], -1.0)], lock=1)
