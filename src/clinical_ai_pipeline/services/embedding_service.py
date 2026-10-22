"""Generate text embeddings using OpenAI's embedding API."""

import logging

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


class EmbeddingServiceError(Exception):
    """Raised when text embedding generation fails."""


class EmbeddingService:
    """Create and validate clinical text embeddings."""

    def __init__(self) -> None:
        """Initialize the OpenAI client using OPENAI_API_KEY."""
        self.client = OpenAI()

    def generate_embedding(self, text: str) -> list[float]:
        """Generate one embedding vector for non-empty text."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must be a non-empty string.")

        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS,
            )

            embedding = response.data[0].embedding

            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise EmbeddingServiceError(
                    "The embedding has an unexpected number of dimensions."
                )

            return embedding

        except (APIConnectionError, APIStatusError) as exc:
            logger.error(
                "OpenAI embedding request failed (%s).",
                type(exc).__name__,
            )
            raise EmbeddingServiceError(
                "Could not generate the text embedding."
            ) from exc
