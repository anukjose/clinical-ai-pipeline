"""Test embedding generation using synthetic, non-clinical text."""

from clinical_ai_pipeline.services.embedding_service import EmbeddingService


def main() -> None:
    service = EmbeddingService()

    embedding = service.generate_embedding(
        "This is a synthetic sentence for testing text embeddings."
    )

    print("Model: text-embedding-3-small")
    print("Embedding dimensions:", len(embedding))
    print("Embedding generated successfully:", bool(embedding))


if __name__ == "__main__":
    main()
