
"""
Ingestion service for the Clinical AI Pipeline.

Responsibilities:
1. Discover medication JSON files from S3.
2. Process each file using the single-file processor.
3. Continue processing when an individual file fails.
4. Collect ingestion results.
5. Provide a summary of the ingestion run.

This service coordinates existing components.
It does not duplicate reading, validation, normalization,
or quarantine logic.
"""

from collections import Counter

from clinical_ai_pipeline.ingestion.models import (
    IngestionResult,
    IngestionStatus,
)
from clinical_ai_pipeline.ingestion.processor import process_file
from clinical_ai_pipeline.storage.s3_client import (
    list_medication_files,
)
from clinical_ai_pipeline.utils.logging_config import (
    get_app_logger,
)

logger = get_app_logger(__name__)


def run_ingestion() -> list[IngestionResult]:
    """
    Process all medication JSON files from S3.

    Returns:
        A list of ingestion results for each file.
    """

    logger.info("Starting ingestion service")

    s3_keys = list_medication_files()

    logger.info(
        "Discovered %s medication files",
        len(s3_keys),
    )

    results: list[IngestionResult] = []

    for index, s3_key in enumerate(s3_keys, start=1):
        logger.info(
            "Processing file %s/%s | s3_key=%s",
            index,
            len(s3_keys),
            s3_key,
        )

        try:
            result = process_file(s3_key)
            results.append(result)

        except Exception as error:
            logger.exception(
                "Unexpected ingestion error | s3_key=%s | error_type=%s",
                s3_key,
                type(error).__name__,
            )

    logger.info(
        "Ingestion service completed | total_files=%s",
        len(results),
    )

    return results


def summarize_ingestion(
    results: list[IngestionResult],
) -> dict[str, int]:
    """
    Summarize ingestion results by status.

    Args:
        results: Results returned by run_ingestion().

    Returns:
        A dictionary containing counts by ingestion status.
    """

    status_counts = Counter(
        result.status.value
        for result in results
    )

    summary = {
        "total_processed": len(results),
        "success": status_counts.get(
            IngestionStatus.SUCCESS.value,
            0,
        ),
        "failed": status_counts.get(
            IngestionStatus.FAILED.value,
            0,
        ),
        "quarantined": status_counts.get(
            IngestionStatus.QUARANTINED.value,
            0,
        ),
    }

    logger.info(
        "Ingestion summary | total=%s | success=%s | failed=%s | quarantined=%s",
        summary["total_processed"],
        summary["success"],
        summary["failed"],
        summary["quarantined"],
    )

    return summary