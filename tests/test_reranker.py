"""Unit tests for the lexical clinical chunk reranker."""

from types import SimpleNamespace

import pytest

from clinical_ai_pipeline.rag.reranker import rerank_chunks


def make_chunk(
    chunk_id: str,
    text: str,
    source_table: str = "clinical_content",
) -> SimpleNamespace:
    """Create a lightweight test chunk."""
    return SimpleNamespace(
        chunk_id=chunk_id,
        chunk_text=text,
        source_table=source_table,
    )


def test_ranks_chunks_by_query_term_overlap():
    """Chunks matching more query terms should rank higher."""
    chunks = [
        make_chunk("history", "Patient attended a routine follow-up."),
        make_chunk("medication", "Medication dosage and frequency recorded."),
        make_chunk("dosage", "Medication dosage recorded."),
    ]

    results = rerank_chunks(
        "medication dosage frequency",
        chunks,
        limit=3,
    )

    assert [chunk.chunk_id for chunk in results] == [
        "medication",
        "dosage",
        "history",
    ]


def test_preserves_original_order_when_scores_tie():
    """Chunks with equal scores should retain their original order."""
    chunks = [
        make_chunk("first", "Medication dosage recorded."),
        make_chunk("second", "Dosage medication recorded."),
    ]

    results = rerank_chunks("medication dosage", chunks)

    assert [chunk.chunk_id for chunk in results] == [
        "first",
        "second",
    ]


def test_respects_result_limit():
    """The reranker should return no more than the requested limit."""
    chunks = [
        make_chunk("one", "Medication"),
        make_chunk("two", "Dosage"),
        make_chunk("three", "Frequency"),
    ]

    results = rerank_chunks(
        "medication dosage frequency",
        chunks,
        limit=2,
    )

    assert len(results) == 2


def test_empty_chunk_list_returns_empty_list():
    """An empty candidate list should return no results."""
    assert rerank_chunks("medication dosage", []) == []


@pytest.mark.parametrize("query", ["", "   "])
def test_rejects_blank_query(query):
    """Blank queries should be rejected."""
    with pytest.raises(ValueError, match="Query must not be empty"):
        rerank_chunks(query, [])


def test_rejects_invalid_limit():
    """A result limit below one should be rejected."""
    with pytest.raises(ValueError, match="Limit must be at least 1"):
        rerank_chunks("medication dosage", [], limit=0)


def test_medication_query_prefers_medication_source():
    """Explicit medication queries should favor medication records."""
    chunks = [
        make_chunk(
            "history",
            "Medication dosage and frequency recorded.",
            source_table="consultation_history",
        ),
        make_chunk(
            "medication",
            "Medication dosage and frequency recorded.",
            source_table="consultation_medications",
        ),
    ]

    results = rerank_chunks(
        "Find medication dosage and frequency information",
        chunks,
        limit=2,
    )

    assert [chunk.chunk_id for chunk in results] == [
        "medication",
        "history",
    ]
