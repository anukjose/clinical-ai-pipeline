"""Unit tests for the clinical RAG service."""

from clinical_ai_pipeline.rag.models import RAGRequest
from clinical_ai_pipeline.rag.service import RAGService
from clinical_ai_pipeline.retrieval.models import RetrievalResponse


def test_returns_insufficient_evidence_when_nothing_is_retrieved():
    """Do not call the LLM when retrieval returns no clinical chunks."""

    class FakeRetrievalService:
        """Return an empty retrieval result without accessing PostgreSQL."""

        def search(self, request):
            return RetrievalResponse(
                query=request.query,
                results=[],
                result_count=0,
            )

    service = RAGService(retrieval_service=FakeRetrievalService())

    response = service.answer(
        RAGRequest(
            question="What medication was recorded?",
            consultation_id=123,
        )
    )

    assert response.insufficient_evidence is True
    assert response.evidence == []
    assert "could not find" in response.answer.lower()
