"""
Test the ingestion processor.

This test:
1. Reads one known JSON file from S3.
2. Runs the complete ingestion workflow.
3. Prints the ingestion result metadata.

Only safe metadata is printed.
"""

from clinical_ai_pipeline.ingestion.processor import (
    process_file,
)
from clinical_ai_pipeline.utils.logging_config import (
    configure_logging,
)


def main() -> None:
    # Configure logging before running the processor.
    configure_logging()

    # Use one known JSON file from our existing S3 bucket.
    s3_key = "raw/medications/ddi-medication_1489_169584.json"

    # Run the complete ingestion workflow for one file.
    result = process_file(s3_key)

    # Print safe processing metadata.
    print("S3 key:", result.s3_key)
    print("Status:", result.status.value)
    print("Records processed:", result.records_processed)
    print("File hash available:", result.file_hash is not None)
    print("Pipeline version:", result.pipeline_version)

    if result.error_message:
        print("Error message:", result.error_message)

    print("Processor test completed")


if __name__ == "__main__":
    main()
