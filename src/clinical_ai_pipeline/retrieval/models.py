"""Request and response models for clinical retrieval.

Why these models matter:
- RetrievalRequest validates incoming searches before they reach the database.
- RetrievedChunk retains source metadata for traceability and future citations.
- similarity_score converts cosine distance into a similarity score.
  This is a mathematical conversion, not a calibrated confidence score.
- RetrievalResponse provides a predictable response format for APIs.
"""

from pydantic import BaseModel, Field, field_validator


class RetrievalRequest(BaseModel):
    """Validate a semantic clinical search request."""

    query: str = Field(
        min_length=1,
        max_length=4000,
        description="The clinical question or search text.",
    )

    consultation_id: int | None = Field(
        default=None,
        gt=0,
        description="Optional consultation ID to restrict the search.",
    )

    source_table: str | None = Field(
        default=None,
        description=(
            "Optional source table to restrict the search, "
            "such as consultation_medications or consultation_history."
        ),
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of matching chunks to return.",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        """Trim the query and reject whitespace-only input."""
        value = value.strip()

        if not value:
            raise ValueError("Query must not be empty.")

        return value

    @field_validator("source_table")
    @classmethod
    def validate_source_table(cls, value: str | None) -> str | None:
        """Reject unsupported clinical source tables."""
        allowed_source_tables = {
            "clinical_content",
            "consultation_history",
            "consultation_diagnosis",
            "consultation_investigations",
            "consultation_medications",
            "consultation_procedures",
        }

        if value is not None and value not in allowed_source_tables:
            raise ValueError("Unsupported clinical source table.")

        return value


class RetrievedChunk(BaseModel):
    """Represent a clinical text chunk retrieved from the database."""

    chunk_id: str
    consultation_id: int
    source_table: str | None = None
    source_record_id: str | None = None
    section_name: str | None = None
    chunk_text: str
    chunk_index: int | None = None
    cosine_distance: float

    @property
    def similarity_score(self) -> float:
        """Convert cosine distance into a cosine similarity score."""
        return 1.0 - self.cosine_distance


class RetrievalResponse(BaseModel):
    """Return ranked clinical search results."""

    query: str
    results: list[RetrievedChunk]
    result_count: int
