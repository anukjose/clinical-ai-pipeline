"""
Ingestion processor for the Clinical AI Pipeline.

Responsibilities:
1. Read a JSON file from S3.
2. Validate the input data.
3. Normalize the validated record.
4. Persist structured clinical data to PostgreSQL.
5. Generate and persist clinical text chunks.
6. Return an IngestionResult.
7. Quarantine records that fail validation.

This component coordinates the ingestion, persistence,
and chunking modules. It processes one S3 file at a time.
"""

from typing import Any

from clinical_ai_pipeline.ingestion.models import (
    IngestionResult,
    IngestionStatus,
)
from clinical_ai_pipeline.ingestion.normalizer import (
    normalize_medication_record,
)
from clinical_ai_pipeline.ingestion.quarantine import (
    quarantine_record,
)
from clinical_ai_pipeline.ingestion.reader import (
    read_and_hash_file,
)
from clinical_ai_pipeline.ingestion.validator import (
    validate_medication_record,
)
from clinical_ai_pipeline.processing.chunker import (
    create_clinical_chunks,
)
from clinical_ai_pipeline.storage.postgres_repository import (
    get_all_clinical_text_sources_for_chunking,
    save_patient_and_consultation,
    save_consultation_vitals,
    save_consultation_medications,
    save_next_review,
    save_consultation_history,
    save_consultation_investigations,
    save_consultation_procedures,
    save_clinical_content,
    save_clinical_chunks,
    get_chunks_missing_embeddings,
    save_chunk_embedding,
)
from clinical_ai_pipeline.services.embedding_service import (
    EmbeddingService,
)

from clinical_ai_pipeline.utils.exceptions import (
    DataValidationError,
)
from clinical_ai_pipeline.utils.logging_config import (
    get_app_logger,
)

# Create a module-specific logger.
logger = get_app_logger(__name__)


# Version of the current ingestion pipeline implementation.
PIPELINE_VERSION = "1.0.0"


def generate_missing_embeddings(
    consultation_id: int,
    batch_size: int = 5,
) -> int:
    """Generate and save embeddings for a consultation's unembedded chunks."""
    embedding_service = EmbeddingService()
    total_embedded = 0

    while True:
        chunks = get_chunks_missing_embeddings(
            consultation_id=consultation_id,
            limit=batch_size,
        )

        if not chunks:
            break

        for chunk in chunks:
            embedding = embedding_service.generate_embedding(chunk["chunk_text"])

            save_chunk_embedding(
                chunk_id=chunk["chunk_id"],
                embedding=embedding,
            )

            total_embedded += 1

        logger.info(
            "Clinical embeddings saved | consultation_id=%s | "
            "batch_embedded=%s | total_embedded=%s",
            consultation_id,
            len(chunks),
            total_embedded,
        )

    return total_embedded


def process_file(s3_key: str) -> IngestionResult:
    """
    Process one JSON file through the ingestion pipeline.

    Workflow:
        Read
        -> Validate
        -> Normalize
        -> Persist structured clinical data
        -> Generate clinical chunks
        -> Persist clinical chunks

    Args:
        s3_key: S3 object key identifying the JSON file.

    Returns:
        An IngestionResult containing the processing status
        and relevant metadata.
    """

    logger.info(
        "Starting ingestion processing | s3_key=%s",
        s3_key,
    )

    file_hash: str | None = None
    data: dict[str, Any] | None = None

    try:
        # Step 1: Read the JSON file and calculate its hash.
        data, file_hash = read_and_hash_file(s3_key)

        # Step 2: Validate the JSON using the Pydantic model.
        validated_record = validate_medication_record(data)

        # Step 3: Normalize the validated record.
        # The normalizer returns a snake_case dictionary.
        normalized_record = normalize_medication_record(validated_record)

        # Get the consultation ID for this record.
        consultation_id = normalized_record["medication_id"]

        # Step 4: Persist the patient and consultation first,
        # because related clinical tables depend on them.
        save_patient_and_consultation(normalized_record)

        # Step 5: Persist the consultation's structured data.
        save_consultation_vitals(normalized_record)
        save_consultation_medications(normalized_record)
        save_next_review(normalized_record)
        save_consultation_history(normalized_record)
        save_consultation_investigations(normalized_record)
        save_consultation_procedures(normalized_record)
        save_clinical_content(normalized_record)

        logger.info(
            "Clinical record persisted successfully | "
            "consultation_id=%s | s3_key=%s",
            consultation_id,
            s3_key,
        )

        # Step 6: Retrieve searchable text for this consultation.
        # The repository function must support filtering by ID.
        text_sources = get_all_clinical_text_sources_for_chunking(
            consultation_id=consultation_id
        )

        # Step 7: Generate chunks for each clinical text source.
        all_chunks: list[dict[str, Any]] = []

        for record in text_sources:
            chunks = create_clinical_chunks(
                text=record["content_text"],
                consultation_id=record["consultation_id"],
                source_table=record["source_table"],
                source_record_id=record["source_record_id"],
                section_name=record["section_name"],
            )

            all_chunks.extend(chunks)

        logger.info(
            "Clinical chunks generated | consultation_id=%s | "
            "text_sources=%s | chunks=%s",
            consultation_id,
            len(text_sources),
            len(all_chunks),
        )

        # Step 8: Persist the generated chunks.
        saved_count = save_clinical_chunks(all_chunks)

        logger.info(
            "Clinical chunk persistence completed | "
            "consultation_id=%s | chunks_saved=%s",
            consultation_id,
            saved_count,
        )
        # Step 9: Generate and persist missing embeddings.
        embeddings_saved = generate_missing_embeddings(
            consultation_id=consultation_id,
        )

        logger.info(
            "Clinical embedding persistence completed | "
            "consultation_id=%s | embeddings_saved=%s",
            consultation_id,
            embeddings_saved,
        )

        # Step 10: Return success only after chunk persistence.
        return IngestionResult(
            s3_key=s3_key,
            file_hash=file_hash,
            status=IngestionStatus.SUCCESS,
            records_processed=1,
            pipeline_version=PIPELINE_VERSION,
        )

    except DataValidationError as error:
        # Validation failures are expected data-quality problems.
        # Quarantine the original data when it was read successfully.
        logger.error(
            "Validation failed | s3_key=%s",
            s3_key,
        )

        try:
            if data is None:
                data, file_hash = read_and_hash_file(s3_key)

            quarantine_path = quarantine_record(
                s3_key=s3_key,
                data=data,
                error_message=str(error),
            )

            logger.info(
                "Validation failure quarantined | path=%s",
                quarantine_path,
            )

        except Exception:
            # Preserve the original validation failure.
            logger.exception(
                "Unable to quarantine validation failure | " "s3_key=%s",
                s3_key,
            )

        return IngestionResult(
            s3_key=s3_key,
            file_hash=file_hash,
            status=IngestionStatus.QUARANTINED,
            records_processed=0,
            error_message="Validation failed",
            pipeline_version=PIPELINE_VERSION,
        )

    except Exception as error:
        # Catch unexpected processing, database, and chunking failures.
        logger.exception(
            "Unexpected ingestion failure | s3_key=%s | " "error_type=%s",
            s3_key,
            type(error).__name__,
        )

        return IngestionResult(
            s3_key=s3_key,
            file_hash=file_hash,
            status=IngestionStatus.FAILED,
            records_processed=0,
            error_message=("Unexpected ingestion processing failure"),
            pipeline_version=PIPELINE_VERSION,
        )
