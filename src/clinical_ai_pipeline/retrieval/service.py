"""Clinical semantic retrieval service."""

import logging
from uuid import UUID

from clinical_ai_pipeline.retrieval.models import (
    RetrievedChunk,
    RetrievalRequest,
    RetrievalResponse,
)
from clinical_ai_pipeline.services.embedding_service import (
    EmbeddingService,
)
from clinical_ai_pipeline.storage.postgres_repository import (
    search_similar_clinical_chunks,
)

logger = logging.getLogger(__name__)


class RetrievalService:
    """Retrieve relevant clinical chunks using semantic similarity."""

    def __init__(self) -> None:
        """Initialize the embedding service."""
        self.embedding_service = EmbeddingService()

    def search(self, request: RetrievalRequest) -> RetrievalResponse:
        """Embed a query and return its most relevant clinical chunks."""
        query_embedding = self.embedding_service.generate_embedding(
            request.query.strip()
        )

        rows = search_similar_clinical_chunks(
            query_embedding=query_embedding,
            limit=request.limit,
            consultation_id=request.consultation_id,
            source_table=request.source_table,
        )

        results = [
            RetrievedChunk(
                chunk_id=str(row["chunk_id"]),
                consultation_id=row["consultation_id"],
                source_table=row["source_table"],
                source_record_id=(
                    str(row["source_record_id"])
                    if row["source_record_id"] is not None
                    else None
                ),
                section_name=row["section_name"],
                chunk_text=row["chunk_text"],
                chunk_index=row["chunk_index"],
                cosine_distance=float(row["cosine_distance"]),
            )
            for row in rows
        ]

        logger.info(
            "Clinical retrieval completed | consultation_id=%s | " "results=%s",
            request.consultation_id,
            len(results),
        )

        return RetrievalResponse(
            query=request.query.strip(),
            results=results,
            result_count=len(results),
        )
