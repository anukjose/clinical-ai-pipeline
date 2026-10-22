
"""
Test the ingestion S3 reader.

This test reads one known S3 file and verifies that:
1. The JSON data is returned.
2. A SHA-256 hash is generated.
3. Logging is working correctly.
"""

from clinical_ai_pipeline.ingestion.reader import read_and_hash_file
from clinical_ai_pipeline.utils.logging_config import configure_logging


def main() -> None:
    # Configure application logging before using the reader.
    configure_logging()

    # Use one known JSON file from our existing S3 bucket.
    s3_key = "raw/medications/ddi-medication_100354_258163.json"

    # Read the file and generate its content hash.
    data, file_hash = read_and_hash_file(s3_key)

    # Print safe metadata instead of the complete patient record.
    print(f"Data type: {type(data).__name__}")
    print(f"Hash length: {len(file_hash)}")
    print(f"SHA-256 hash: {file_hash}")


if __name__ == "__main__":
    main()