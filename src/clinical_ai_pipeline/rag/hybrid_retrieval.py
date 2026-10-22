"""Hybrid clinical retrieval using Reciprocal Rank Fusion (RRF)."""

import logging
from typing import Any

from pydantic import BaseModel, Field, field_validator
from clinical_ai_pipeline.rag.reranker import rerank_chunks

from clinical_ai_pipeline.retrieval.models import RetrievalRequest
from clinical_ai_pipeline.services.embedding_service import EmbeddingService
from clinical_ai_pipeline.storage.postgres_repository import (
    search_keyword_clinical_chunks,
    search_similar_clinical_chunks,
)

logger = logging.getLogger(__name__)

# A common RRF smoothing constant. We will evaluate this later.
RRF_K = 60


class HybridRetrievalRequest(BaseModel):
    """Validated request for hybrid clinical retrieval."""

    query: str = Field(min_length=1, max_length=4000)
    consultation_id: int | None = Field(default=None, gt=0)
    limit: int = Field(default=5, ge=1, le=100)
    source_table: str | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        """Trim whitespace and reject blank queries."""
        value = value.strip()
        if not value:
            raise ValueError("Query must not be empty.")
        return value


class HybridRetrievedChunk(BaseModel):
    """A clinical chunk ranked using semantic and keyword retrieval."""

    chunk_id: str
    consultation_id: int
    source_table: str | None = None
    source_record_id: str | None = None
    section_name: str | None = None
    chunk_text: str
    chunk_index: int | None = None

    # Rank positions are one-based; None means that search did not find it.
    semantic_rank: int | None = None
    keyword_position: int | None = None
    rrf_score: float


class HybridRetrievalResponse(BaseModel):
    """Return hybrid-ranked chunks and the original query."""

    query: str
    results: list[HybridRetrievedChunk]
    result_count: int


def reciprocal_rank_fusion(
    semantic_rows: list[dict[str, Any]],
    keyword_rows: list[dict[str, Any]],
    limit: int,
    k: int = RRF_K,
) -> list[HybridRetrievedChunk]:
    """Merge two ranked lists, deduplicate chunks, and calculate RRF scores."""
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100.")

    if k < 1:
        raise ValueError("RRF k must be positive.")

    # Store one combined entry per chunk.
    merged: dict[str, dict[str, Any]] = {}

    def add_ranked_rows(
        rows: list[dict[str, Any]],
        rank_field: str,
    ) -> None:
        """Add a ranking list while preserving the best position per chunk."""
        for rank, row in enumerate(rows, start=1):
            chunk_id = str(row["chunk_id"])

            if chunk_id not in merged:
                merged[chunk_id] = {
                    "chunk_id": chunk_id,
                    "consultation_id": row["consultation_id"],
                    "source_table": row.get("source_table"),
                    "source_record_id": (
                        str(row["source_record_id"])
                        if row.get("source_record_id") is not None
                        else None
                    ),
                    "section_name": row.get("section_name"),
                    "chunk_text": row["chunk_text"],
                    "chunk_index": row.get("chunk_index"),
                    "semantic_rank": None,
                    "keyword_position": None,
                    "rrf_score": 0.0,
                }

            # Add this list's RRF contribution.
            merged[chunk_id]["rrf_score"] += 1.0 / (k + rank)

            # Keep the rank from each retrieval method.
            merged[chunk_id][rank_field] = rank

    add_ranked_rows(semantic_rows, "semantic_rank")
    add_ranked_rows(keyword_rows, "keyword_position")

    ranked = [HybridRetrievedChunk(**item) for item in merged.values()]

    ranked.sort(key=lambda item: item.rrf_score, reverse=True)
    return ranked[:limit]


class HybridRetrievalService:
    """Retrieve clinical evidence using semantic and keyword search."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        """Allow embedding-service injection for testing."""
        self.embedding_service = embedding_service or EmbeddingService()

    def search(
        self,
        request: HybridRetrievalRequest,
    ) -> HybridRetrievalResponse:
        """Run both searches and combine their rankings with RRF."""
        query = request.query.strip()

        # Retrieve more candidates than the final result limit so fusion
        # has a broader pool to rank. Respect repository limits.
        candidate_limit = min(100, request.limit * 3)

        query_embedding = self.embedding_service.generate_embedding(query)

        semantic_rows = search_similar_clinical_chunks(
            query_embedding=query_embedding,
            limit=candidate_limit,
            consultation_id=request.consultation_id,
            source_table=request.source_table,
        )

        keyword_rows = search_keyword_clinical_chunks(
            query=query,
            limit=candidate_limit,
            consultation_id=request.consultation_id,
            source_table=request.source_table,
        )

        # Combine semantic and keyword results using Reciprocal Rank Fusion.

        fused_chunks = reciprocal_rank_fusion(
            semantic_rows=semantic_rows,
            keyword_rows=keyword_rows,
            limit=candidate_limit,
        )

        # Rerank the fused candidates against the original user query.
        reranked_chunks = rerank_chunks(
            query=query,
            chunks=fused_chunks,
            limit=request.limit,
        )

        logger.info(
            "Hybrid retrieval and reranking completed: "
            "semantic=%s keyword=%s fused=%s final=%s",
            len(semantic_rows),
            len(keyword_rows),
            len(fused_chunks),
            len(reranked_chunks),
        )

        return HybridRetrievalResponse(
            query=query,
            results=reranked_chunks,
            result_count=len(reranked_chunks),
        )
