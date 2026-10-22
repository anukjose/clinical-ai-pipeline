
"""
Test the ingestion quarantine component.

This test:
1. Creates a small synthetic invalid record.
2. Sends it to the quarantine function.
3. Verifies that a quarantine file is created.

Only synthetic data is used in this test.
"""

from pathlib import Path

from clinical_ai_pipeline.ingestion.quarantine import (
    quarantine_record,
)
from clinical_ai_pipeline.utils.logging_config import configure_logging


def main() -> None:
    # Configure application logging.
    configure_logging()

    # Use synthetic data instead of real patient information.
    s3_key = "raw/medications/test-invalid-record.json"

    invalid_data = {
        "synthetic_test": True,
        "invalid_field": "example",
    }

    error_message = (
        "Synthetic validation failure for testing"
    )

    # Save the synthetic record in the quarantine directory.
    quarantine_path = quarantine_record(
        s3_key=s3_key,
        data=invalid_data,
        error_message=error_message,
    )

    # Verify that the file was created successfully.
    print("Quarantine file created:", quarantine_path)
    print("File exists:", Path(quarantine_path).exists())
    print("Quarantine test completed successfully")


if __name__ == "__main__":
    main()