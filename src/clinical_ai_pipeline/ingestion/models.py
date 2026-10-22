
"""
Data models for the clinical data ingestion service.

This module defines:
1. The possible stages of an ingestion process.
2. The result generated after processing an S3 file.

Pydantic is used to validate the structure and values
of our ingestion metadata.
"""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class IngestionStatus(StrEnum):
    """
    Represents the lifecycle of an ingestion operation.

    Using predefined statuses prevents inconsistent
    status values across the application.
    """

    # File has been identified but processing has not started.
    DISCOVERED = "discovered"

    # File is currently being processed.
    PROCESSING = "processing"

    # File was processed successfully.
    SUCCESS = "success"

    # Processing failed because of a technical or unexpected error.
    FAILED = "failed"

    # File contains invalid data and has been isolated for review.
    QUARANTINED = "quarantined"


class IngestionResult(BaseModel):
    """
    Stores the outcome and metadata of processing one S3 file.

    This model tracks ingestion progress and errors.
    It does not contain the complete patient or medication data.
    """

    # S3 object key identifying the file being processed.
    s3_key: str

    # Hash of the file contents.
    # This can be used later to detect duplicate or changed files.
    # None means the hash has not been calculated yet.
    file_hash: str | None = None

    # Current status of the ingestion operation.
    # This field is required.
    status: IngestionStatus

    # Number of records successfully processed.
    # ge=0 ensures that negative values are rejected.
    records_processed: int = Field(default=0, ge=0)

    # Stores an error description when processing fails.
    # None means that no error was recorded.
    error_message: str | None = None

    # Identifies the version of our ingestion pipeline.
    # Useful for auditing and troubleshooting future changes.
    pipeline_version: str = "1.0.0"

    # Records when the ingestion operation was completed or updated.
    # UTC is used so timestamps remain consistent across environments.
    # default_factory generates a new timestamp for each model instance.
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )