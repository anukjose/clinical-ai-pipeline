
"""
S3 reader for the Clinical AI Pipeline.

Responsibilities:
1. Read a JSON file from S3 using the existing S3 client.
2. Calculate a SHA-256 hash for the file content.
3. Log important processing events.
4. Raise meaningful custom exceptions when reading fails.

This module does not validate or normalize clinical data.
Those responsibilities belong to separate ingestion components.
"""

import hashlib
import json

from clinical_ai_pipeline.storage.s3_client import read_json_file
from clinical_ai_pipeline.utils.exceptions import S3StorageError
from clinical_ai_pipeline.utils.logging_config import get_app_logger


# Create a logger specific to this module.
# The central logging configuration controls how messages are displayed.
logger = get_app_logger(__name__)


def read_and_hash_file(s3_key: str) -> tuple[dict, str]:
    """
    Read one JSON file from S3 and calculate its SHA-256 hash.

    Args:
        s3_key: The S3 object key identifying the JSON file.

    Returns:
        A tuple containing:
        - The JSON data as a dictionary.
        - The SHA-256 hash of the serialized JSON content.

    Raises:
        S3StorageError: If reading or processing the S3 file fails.
    """

    # Log the file key, but never log patient or clinical information.
    logger.info("Reading file from S3: %s", s3_key)

    try:
        # Reuse the existing S3 client.
        # It handles downloading and parsing the JSON file.
        data = read_json_file(s3_key)

        # Serialize the dictionary consistently.
        # Sorting keys ensures stable hashing for the same content.
        serialized_data = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        # Generate a SHA-256 hash from the serialized JSON.
        # This will help us detect duplicate or changed content later.
        file_hash = hashlib.sha256(serialized_data).hexdigest()

        # Log successful reading without exposing sensitive data.
        logger.info(
            "Successfully read S3 file: %s",
            s3_key,
        )

        # Return the data and hash to the next ingestion stage.
        return data, file_hash

    except Exception as error:
        # Log the exception together with its traceback.
        # Avoid logging the actual JSON content or patient information.
        logger.exception(
            "Failed to read S3 file: %s | error_type=%s",
            s3_key,
            type(error).__name__,
        )

        # Convert the low-level error into an application-specific error.
        # 'from error' preserves the original cause for debugging.
        raise S3StorageError(
            f"Unable to read S3 file: {s3_key}"
        ) from error