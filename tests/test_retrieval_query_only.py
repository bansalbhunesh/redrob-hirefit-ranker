import numpy as np

import bm25s

import redrob_ranker.retrieval as retrieval
from redrob_ranker.constants import JD_QUERY
from redrob_ranker.text import tokenize


def test_query_only_bm25_is_bit_exact_with_bm25s_index():
    texts = [
        "Built BM25 search, learning to rank, and vector database retrieval in production.",
        "Python machine learning engineer with recommendation systems experience.",
        "Marketing manager and content writer with no software delivery history.",
        "Information retrieval retrieval retrieval, semantic search, and LLM production.",
        "",
    ]
    tokenized = [tokenize(text) for text in texts]
    reference = bm25s.BM25()
    reference.index(tokenized, show_progress=False)
    expected = np.asarray(reference.get_scores(tokenize(JD_QUERY)), dtype=np.float32)

    actual = retrieval._bm25s_scores(texts, JD_QUERY)

    assert actual.dtype == np.float32
    assert np.array_equal(actual, expected)


def test_query_stats_match_full_tokenizer(monkeypatch):
    text = (
        "Built semantic search and vector database systems. "
        "The search service used BM25 BM25 and learning to rank."
    )
    query_tokens = tokenize(JD_QUERY)
    unique = tuple(dict.fromkeys(query_tokens))
    index = {token: column for column, token in enumerate(unique)}
    monkeypatch.setattr(retrieval, "_QUERY_TOKEN_INDEX", index)

    length, frequencies = retrieval._query_term_stats(text)
    full_tokens = tokenize(text)

    assert length == len(full_tokens)
    assert frequencies == tuple(full_tokens.count(token) for token in unique)


def test_candidate_text_batch_matches_scalar_renderer():
    candidates = [
        {
            "candidate_id": "CAND_1",
            "profile": {
                "current_title": "Search Engineer",
                "summary": "Built semantic retrieval",
            },
            "career_history": [
                {"title": "Engineer", "description": "Shipped BM25", "duration_months": 24}
            ],
            "skills": [{"name": "Python", "proficiency": "advanced"}],
            "redrob_signals": {},
        },
        {"candidate_id": "CAND_2", "profile": {}, "career_history": []},
    ]

    assert retrieval._candidate_text_all(candidates) == [
        retrieval.candidate_text(candidate) for candidate in candidates
    ]
