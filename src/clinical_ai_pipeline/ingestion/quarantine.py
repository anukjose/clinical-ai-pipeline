
"""
Quarantine component for the Clinical AI Pipeline.

Responsibilities:
1. Save files that fail ingestion processing.
2. Preserve the original data for investigation.
3. Store a safe error description.
4. Prevent one problematic file from stopping the batch.

This initial implementation stores quarantined files locally.
A future version can store them in a restricted S3 location.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clinical_ai_pipeline.utils.logging_config import get_app_logger


# Create a module-specific logger.
logger = get_app_logger(__name__)


# Local directory used to store quarantined files during development.
QUARANTINE_DIRECTORY = Path("data/quarantine")


def _create_safe_filename(s3_key: str) -> str:
    """
    Convert an S3 key into a safe filename.

    Args:
        s3_key: Original S3 object key.

    Returns:
        A filename that does not contain directory separators.

    Notes:
        This function prevents the S3 key from creating
        unexpected nested directories.
    """

    # Replace characters other than letters, numbers, dots,
    # hyphens, and underscores with an underscore.
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", s3_key)

    return safe_name


def quarantine_record(
    s3_key: str,
    data: dict[str, Any],
    error_message: str,
) -> Path:
    """
    Save a failed ingestion record to the quarantine directory.

    Args:
        s3_key: S3 key of the problematic file.
        data: JSON data associated with the failed record.
        error_message: Safe description of the processing failure.

    Returns:
        Path to the quarantined file.

    Raises:
        OSError:
            If the quarantine file cannot be written.
    """

    logger.info(
        "Starting quarantine process | s3_key=%s",
        s3_key,
    )

    # Create the quarantine directory if it does not exist.
    QUARANTINE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Generate a safe filename from the original S3 key.
    safe_filename = _create_safe_filename(s3_key)

    # Add a UTC timestamp to avoid overwriting earlier quarantine files.
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    quarantine_filename = (
        f"{timestamp}_{safe_filename}"
    )

    quarantine_path = (
        QUARANTINE_DIRECTORY / quarantine_filename
    )

    # Store the original data and processing metadata together.
    quarantine_payload = {
        "source_s3_key": s3_key,
        "error_message": error_message,
        "quarantined_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }

    # Write the quarantine payload as readable JSON.
    # Clinical data is preserved for authorized investigation.
    with quarantine_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            quarantine_payload,
            file,
            indent=2,
            default=str,
        )

    logger.info(
        "Record quarantined successfully | filename=%s",
        quarantine_filename,
    )

    # Return the path so the calling processor can track the result.
    return quarantine_path