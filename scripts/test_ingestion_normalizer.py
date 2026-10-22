
"""
Test the ingestion normalization component.

This test:
1. Reads a JSON file from S3.
2. Validates the JSON using MedicationRecord.
3. Normalizes the validated record.
4. Prints safe structural information.
"""

from clinical_ai_pipeline.ingestion.reader import read_and_hash_file
from clinical_ai_pipeline.ingestion.validator import (
    validate_medication_record,
)
from clinical_ai_pipeline.ingestion.normalizer import (
    normalize_medication_record,
)
from clinical_ai_pipeline.utils.logging_config import configure_logging


def main() -> None:
    # Configure application logging before running the pipeline.
    configure_logging()

    # Use one known JSON file from our existing S3 bucket.
    s3_key = "raw/medications/ddi-medication_100354_258163.json"

    # Step 1: Read the JSON file and calculate its content hash.
    data, _file_hash = read_and_hash_file(s3_key)

    # Step 2: Validate the dictionary using the Pydantic model.
    validated_record = validate_medication_record(data)

    # Step 3: Normalize the validated medication record.
    normalized_record = normalize_medication_record(
        validated_record
    )

    # Print safe structural information instead of clinical data.
    print(
        "Normalized type:",
        type(normalized_record).__name__,
    )

    print(
        "Top-level fields:",
        list(normalized_record.keys()),
    )

    print(
        "Doctor fields:",
        list(normalized_record["doctor"].keys()),
    )

    print(
        "Patient fields:",
        list(normalized_record["patient"].keys()),
    )

    # Count prescription sections without displaying their contents.
    print(
        "Prescription section count:",
        len(normalized_record["prescription"]),
    )

    print("Normalization completed successfully")


if __name__ == "__main__":
    main()