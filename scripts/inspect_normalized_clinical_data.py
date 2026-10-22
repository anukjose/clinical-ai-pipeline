
"""
Inspect the normalized structure of next_review and vitals.

This script prints field names and data types,
not the actual clinical values.
"""

from clinical_ai_pipeline.storage.s3_client import (
    list_medication_files,
)
from clinical_ai_pipeline.storage.s3_client import (
    read_json_file,
)
from clinical_ai_pipeline.ingestion.validator import (
    validate_medication_record,
)
from clinical_ai_pipeline.ingestion.normalizer import (
    normalize_medication_record,
)
from clinical_ai_pipeline.utils.logging_config import (
    configure_logging,
)


def main():
    configure_logging()

    # Read one file from S3.
    files = list_medication_files()

    if not files:
        raise RuntimeError("No medication files found.")

    #data = read_json_file(files[0])
    # Read the specific medication file from S3.
    s3_key = "raw/medications/ddi-medication_1489_169584.json"

    data = read_json_file(s3_key)

    # Validate and normalize the record.
    validated_record = validate_medication_record(data)
    normalized_record = normalize_medication_record(
        validated_record
    )

    print("\n===== NORMALIZED STRUCTURE =====")

    # Inspect next_review.
    next_review = normalized_record["next_review"]

    print("\nNext review type:", type(next_review).__name__)

    if isinstance(next_review, dict):
        print("Next review fields:", list(next_review.keys()))

    # Inspect prescription sections.
    for section in normalized_record["prescription"]:
        if section["section_name"] in ["Vitals", "Next Review", "Medicine"]:
            print(
                "\nSection:",
                section["section_name"],
            )

            print(
                "Number of items:",
                len(section["data"]),
            )

            if section["data"]:
                first_item = section["data"][0]

                print(
                    "First item fields:",
                    list(first_item.keys()),
                )

                print(
                    "Field types:",
                    {
                        key: type(value).__name__
                        for key, value in first_item.items()
                    },
                )

    print("\n================================")


if __name__ == "__main__":
    main()