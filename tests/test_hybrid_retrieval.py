"""Unit tests for hybrid clinical retrieval."""

from clinical_ai_pipeline.rag.hybrid_retrieval import (
    reciprocal_rank_fusion,
)


def make_chunk(chunk_id: str, text: str) -> dict:
    """Create a sample retrieval result for testing."""
    return {
        "chunk_id": chunk_id,
        "consultation_id": 101,
        "source_table": "consultation_medications",
        "source_record_id": "record-1",
        "section_name": "medications",
        "chunk_text": text,
        "chunk_index": 0,
    }


def test_rrf_combines_semantic_and_keyword_results():
    """A chunk found by both methods should receive both contributions."""
    semantic_rows = [
        make_chunk("chunk-A", "Medication dosage information"),
        make_chunk("chunk-B", "Consultation history"),
    ]

    keyword_rows = [
        make_chunk("chunk-B", "Consultation history"),
        make_chunk("chunk-C", "Medication frequency"),
    ]

    results = reciprocal_rank_fusion(
        semantic_rows=semantic_rows,
        keyword_rows=keyword_rows,
        limit=3,
    )

    # chunk-B ranks second semantically and first by keywords.
    # Its combined score should exceed chunks found by only one method.
    assert results[0].chunk_id == "chunk-B"
    assert results[0].semantic_rank == 2
    assert results[0].keyword_position == 1

    assert results[1].chunk_id == "chunk-A"
    assert results[1].semantic_rank == 1
    assert results[1].keyword_position is None

    assert results[2].chunk_id == "chunk-C"
    assert results[2].semantic_rank is None
    assert results[2].keyword_position == 2


def test_rrf_deduplicates_chunks():
    """A chunk present in both result lists should appear only once."""
    chunk = make_chunk("chunk-A", "Medication dosage information")

    results = reciprocal_rank_fusion(
        semantic_rows=[chunk],
        keyword_rows=[chunk],
        limit=5,
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-A"


def test_rrf_returns_empty_results_for_empty_inputs():
    """No retrieval matches should produce an empty list."""
    results = reciprocal_rank_fusion(
        semantic_rows=[],
        keyword_rows=[],
        limit=5,
    )

    assert results == []


def test_rrf_rejects_invalid_limit():
    """Invalid result limits should be rejected."""
    try:
        reciprocal_rank_fusion(
            semantic_rows=[],
            keyword_rows=[],
            limit=0,
        )
    except ValueError as exc:
        assert "Limit must be between 1 and 100" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid limit")


from unittest.mock import Mock

from clinical_ai_pipeline.rag.hybrid_retrieval import (
    HybridRetrievalService,
)
from clinical_ai_pipeline.retrieval.models import RetrievalRequest


def test_hybrid_service_combines_both_search_methods(monkeypatch):
    """Verify that semantic and keyword results are fused correctly."""

    semantic_rows = [
        {
            "chunk_id": "chunk-A",
            "consultation_id": 101,
            "source_table": "consultation_medications",
            "source_record_id": "record-1",
            "section_name": "medications",
            "chunk_text": "Medication dosage information",
            "chunk_index": 0,
        }
    ]

    keyword_rows = [
        {
            "chunk_id": "chunk-A",
            "consultation_id": 101,
            "source_table": "consultation_medications",
            "source_record_id": "record-1",
            "section_name": "medications",
            "chunk_text": "Medication dosage information",
            "chunk_index": 0,
        },
        {
            "chunk_id": "chunk-B",
            "consultation_id": 101,
            "source_table": "consultation_history",
            "source_record_id": "record-2",
            "section_name": "history",
            "chunk_text": "Treatment frequency information",
            "chunk_index": 1,
        },
    ]

    embedding_service = Mock()
    embedding_service.generate_embedding.return_value = [0.1] * 1536

    semantic_search = Mock(return_value=semantic_rows)
    keyword_search = Mock(return_value=keyword_rows)

    monkeypatch.setattr(
        "clinical_ai_pipeline.rag.hybrid_retrieval.search_similar_clinical_chunks",
        semantic_search,
    )
    monkeypatch.setattr(
        "clinical_ai_pipeline.rag.hybrid_retrieval.search_keyword_clinical_chunks",
        keyword_search,
    )

    service = HybridRetrievalService(
        embedding_service=embedding_service,
    )

    request = RetrievalRequest(
        query="  medication dosage and frequency  ",
        consultation_id=101,
        limit=5,
        source_table="consultation_medications",
    )

    response = service.search(request)

    # The query should be trimmed before embedding and keyword search.
    embedding_service.generate_embedding.assert_called_once_with(
        "medication dosage and frequency"
    )

    # Both retrieval methods should receive the same filters.
    semantic_search.assert_called_once_with(
        query_embedding=[0.1] * 1536,
        limit=15,
        consultation_id=101,
        source_table="consultation_medications",
    )

    keyword_search.assert_called_once_with(
        query="medication dosage and frequency",
        limit=15,
        consultation_id=101,
        source_table="consultation_medications",
    )

    assert response.query == "medication dosage and frequency"
    assert response.result_count == 2
    assert response.results[0].chunk_id == "chunk-A"
    assert response.results[0].semantic_rank == 1
    assert response.results[0].keyword_position == 1


def test_hybrid_service_returns_empty_when_both_searches_find_nothing(
    monkeypatch,
):
    """Verify that empty search results produce an empty response."""

    embedding_service = Mock()
    embedding_service.generate_embedding.return_value = [0.1] * 1536

    monkeypatch.setattr(
        "clinical_ai_pipeline.rag.hybrid_retrieval.search_similar_clinical_chunks",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(
        "clinical_ai_pipeline.rag.hybrid_retrieval.search_keyword_clinical_chunks",
        Mock(return_value=[]),
    )

    service = HybridRetrievalService(
        embedding_service=embedding_service,
    )

    response = service.search(
        RetrievalRequest(query="unknown clinical information", limit=5)
    )

    assert response.results == []
    assert response.result_count == 0
