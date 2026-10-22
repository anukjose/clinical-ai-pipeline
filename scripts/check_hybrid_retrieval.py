"""Manually test hybrid retrieval against PostgreSQL."""

from clinical_ai_pipeline.rag.hybrid_retrieval import (
    HybridRetrievalRequest,
    HybridRetrievalService,
)


def main() -> None:
    service = HybridRetrievalService()

    request = HybridRetrievalRequest(
        query="Find medication dosage and frequency information",
        limit=5,
    )

    response = service.search(request)

    print(f"Query: {response.query}")
    print(f"Number of results: {response.result_count}")

    for index, chunk in enumerate(response.results, start=1):
        print(f"\nResult {index}")
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Source table: {chunk.source_table}")
        print(f"Semantic rank: {chunk.semantic_rank}")
        print(f"Keyword rank: {chunk.keyword_position}")
        print(f"RRF score: {chunk.rrf_score:.6f}")
        print(f"Text preview: {chunk.chunk_text[:150]}")


if __name__ == "__main__":
    main()
