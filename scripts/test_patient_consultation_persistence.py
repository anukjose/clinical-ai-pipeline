"""
Test saving one normalized medication record
into PostgreSQL.
"""

from clinical_ai_pipeline.storage.s3_client import (
    list_medication_files,
)
from clinical_ai_pipeline.ingestion.reader import (
    read_and_hash_file,
)
from clinical_ai_pipeline.ingestion.validator import (
    validate_medication_record,
)
from clinical_ai_pipeline.ingestion.normalizer import (
    normalize_medication_record,
)
from clinical_ai_pipeline.storage.postgres_repository import (
    save_patient_and_consultation,
)
from clinical_ai_pipeline.utils.logging_config import (
    configure_logging,
)
from clinical_ai_pipeline.storage.postgres_repository import (
    save_consultation_vitals,
)

from clinical_ai_pipeline.storage.postgres_repository import (
    save_consultation_medications,
)

from clinical_ai_pipeline.storage.postgres_repository import (
    save_consultation_medications,
    save_next_review,
    save_consultation_history,
    save_consultation_investigations,
    save_consultation_procedures,
    save_clinical_content,
)


def main():
    configure_logging()

    # Get the available medication files from S3.
    files = list_medication_files()

    if not files:
        raise RuntimeError("No medication files found in S3.")

    # Select one file for the initial persistence test.
    # s3_key = files[0]
    # Read the specific medication file from S3.
    s3_key = "raw/medications/ddi-medication_1489_169584.json"

    # Read the original JSON data.
    data, file_hash = read_and_hash_file(s3_key)

    # Validate the original data using Pydantic.
    validated_record = validate_medication_record(data)

    # Convert the validated record into normalized data.
    normalized_record = normalize_medication_record(validated_record)

    # Save the patient and consultation in PostgreSQL.
    save_patient_and_consultation(normalized_record)

    # Save the consultation's vital signs.
    save_consultation_vitals(normalized_record)

    # Save the consultation's medication records.
    save_consultation_medications(normalized_record)

    # Save the consultation's next review information.
    save_next_review(normalized_record)

    # Save the consultation's history notes.
    save_consultation_history(normalized_record)

    # Save investigation records.
    save_consultation_investigations(normalized_record)

    # Save procedure records.
    save_consultation_procedures(normalized_record)

    # Save selected clinical content sections.
    save_clinical_content(normalized_record)

    print("Patient and consultation saved successfully!")
    print("File hash available:", bool(file_hash))


if __name__ == "__main__":
    main()
