
"""
Test the ingestion validation component.

This test:
1. Reads a known JSON file from S3.
2. Validates the JSON using MedicationRecord.
3. Prints safe metadata from the validated object.
"""

from clinical_ai_pipeline.ingestion.reader import read_and_hash_file
from clinical_ai_pipeline.ingestion.validator import (
    validate_medication_record,
)
from clinical_ai_pipeline.utils.logging_config import configure_logging


def main() -> None:
    # Configure logging before starting the workflow.
    configure_logging()

    # Use one known JSON file from the existing S3 bucket.
    s3_key = "raw/medications/ddi-medication_100354_258163.json"

    # Read the JSON file and calculate its content hash.
    data, file_hash = read_and_hash_file(s3_key)

    # Validate the dictionary using the MedicationRecord model.
    validated_record = validate_medication_record(data)

    # Print safe metadata instead of the complete clinical record.
    print(f"Validated type: {type(validated_record).__name__}")
    print(f"Medication ID: {validated_record.medicationId}")
    print(f"Hash length: {len(file_hash)}")
    print("Validation completed successfully")


if __name__ == "__main__":
    main()