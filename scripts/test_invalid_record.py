from clinical_ai_pipeline.ingestion.validator import validate_medication_record
from clinical_ai_pipeline.ingestion.quarantine import quarantine_record
from clinical_ai_pipeline.utils.exceptions import DataValidationError
from clinical_ai_pipeline.utils.logging_config import configure_logging


def main():
    configure_logging()

    # Synthetic invalid record for testing validation failure.
    invalid_record = {
        "medicationId": "invalid-id",
        "consultationDate": "2026-09-19",
    }

    s3_key = "raw/medications/test-invalid-record.json"

    try:
        validate_medication_record(invalid_record)

    except DataValidationError as error:
        print("Validation failed as expected.")

        quarantine_path = quarantine_record(
            s3_key=s3_key,
            data=invalid_record,
            error_message=str(error),
        )

        print("Quarantine file created:", quarantine_path)
        print("Quarantine test completed successfully.")


if __name__ == "__main__":
    main()