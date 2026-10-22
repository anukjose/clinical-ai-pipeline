
from pydantic import ValidationError

from clinical_ai_pipeline.processing.models import MedicationRecord
from clinical_ai_pipeline.storage.s3_client import (
    list_medication_files,
    read_json_file,
)


def main() -> None:
    s3_keys = list_medication_files()

    total_files = len(s3_keys)
    valid_files = 0
    invalid_files = 0

    print(f"Total files found: {total_files}")
    print("Starting validation...\n")

    for index, s3_key in enumerate(s3_keys, start=1):
        try:
            data = read_json_file(s3_key)

            MedicationRecord.model_validate(data)

            valid_files += 1

        except ValidationError as error:
            invalid_files += 1

            print(f"Validation failed: {s3_key}")
            print(f"Error count: {len(error.errors())}\n")

        except Exception as error:
            invalid_files += 1

            print(f"Processing failed: {s3_key}")
            print(f"Error type: {type(error).__name__}\n")

        if index % 100 == 0:
            print(f"Processed {index}/{total_files} files")

    print("\nValidation Summary")
    print("-" * 30)
    print(f"Total files: {total_files}")
    print(f"Valid files: {valid_files}")
    print(f"Invalid files: {invalid_files}")


if __name__ == "__main__":
    main()