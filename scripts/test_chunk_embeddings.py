"""Test embedding generation and storage for one consultation."""

from clinical_ai_pipeline.services.embedding_service import EmbeddingService
from clinical_ai_pipeline.storage.postgres_repository import (
    get_chunks_missing_embeddings,
    save_chunk_embedding,
)


def main() -> None:
    consultation_id = 169584
    batch_size = 5

    # Retrieve at most five chunks without embeddings.
    chunks = get_chunks_missing_embeddings(
        consultation_id=consultation_id,
        limit=batch_size,
    )

    if not chunks:
        print("No chunks are missing embeddings for this consultation.")
        return

    print(f"Chunks retrieved: {len(chunks)}")

    embedding_service = EmbeddingService()

    for chunk in chunks:
        # Do not print clinical text or patient information.
        embedding = embedding_service.generate_embedding(chunk["chunk_text"])

        save_chunk_embedding(
            chunk_id=chunk["chunk_id"],
            embedding=embedding,
        )

        print(
            f"Saved embedding for chunk {chunk['chunk_id']}; "
            f"dimensions: {len(embedding)}"
        )

    print("Embedding test completed.")


if __name__ == "__main__":
    main()
