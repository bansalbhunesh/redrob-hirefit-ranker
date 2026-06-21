"""redrob_ranker_v2 — a clean-room Learning-to-Rank model.

This is a *separate model*, not a re-tuning of the hand-weighted linear blend in
`redrob_ranker`. The scorer is a LightGBM LambdaMART ranker trained on the label
signal; the old pipeline's hand-set `BASE_FEATURE_WEIGHTS` are not used. Shared
*infrastructure* (JSONL I/O, candidate-text rendering, BM25 retrieval, the
feature extractor, integrity rules, reasoning) is imported rather than
reinvented — those are data-prep and rules, not the model.

Public entry point: `redrob_ranker_v2.pipeline_v2.run_ranking_v2`.
"""

from redrob_ranker_v2.model import LearnedRanker, V2_FEATURES

__all__ = ["LearnedRanker", "V2_FEATURES"]
