"""Redrob candidate ranker."""

__all__ = ["RankerConfig", "RankingResult", "run_ranking"]


def __getattr__(name: str):
    if name in __all__:
        from redrob_ranker.pipeline import RankerConfig, RankingResult, run_ranking

        exports = {
            "RankerConfig": RankerConfig,
            "RankingResult": RankingResult,
            "run_ranking": run_ranking,
        }
        return exports[name]
    raise AttributeError(f"module 'redrob_ranker' has no attribute {name!r}")
