"""Request and response models for clinical RAG."""

from pydantic import BaseModel, Field, field_validator


class RAGRequest(BaseModel):
    """Validate a question submitted to the clinical RAG service."""

    question: str = Field(
        min_length=3,
        max_length=4000,
        description="Question to answer using retrieved clinical evidence.",
    )

    consultation_id: int | None = Field(
        default=None,
        gt=0,
        description="Optional consultation ID to restrict retrieval.",
    )

    retrieval_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of evidence chunks to retrieve.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """Reject questions containing only whitespace."""
        value = value.strip()

        if not value:
            raise ValueError("Question must not be empty.")

        return value


class EvidenceReference(BaseModel):
    """Identify a retrieved clinical chunk used as evidence."""

    chunk_id: str
    consultation_id: int
    source_table: str | None = None
    source_record_id: str | None = None
    section_name: str | None = None
    chunk_text: str
    similarity_score: float


class RAGResponse(BaseModel):
    """Return a generated answer with traceable supporting evidence."""

    question: str
    answer: str
    evidence: list[EvidenceReference] = Field(default_factory=list)
    insufficient_evidence: bool = False
