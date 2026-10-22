"""
Test retrieving clinical content from PostgreSQL.
"""

from clinical_ai_pipeline.storage.postgres_repository import (
    get_clinical_content_for_chunking,
)


def main():
    # Retrieve clinical content from PostgreSQL.
    records = get_clinical_content_for_chunking()

    # Check that the function returns a list.
    assert isinstance(records, list)

    print("Retrieval function executed successfully.")
    print("Total clinical content records retrieved:", len(records))

    # Check the structure without printing clinical text.
    if records:
        expected_fields = {
            "source_record_id",
            "consultation_id",
            "section_name",
            "content_text",
            "source_table",
        }

        assert expected_fields.issubset(records[0].keys())

        print("Record structure verified.")
        print("Source table:", records[0]["source_table"])
        print("Section name available:", bool(records[0]["section_name"]))
        print("Source record ID available:", bool(records[0]["source_record_id"]))

    else:
        print("No clinical content records found.")


if __name__ == "__main__":
    main()
