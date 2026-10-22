"""
Test retrieving searchable text from all six clinical tables.
"""

from collections import Counter

from clinical_ai_pipeline.storage.postgres_repository import (
    get_all_clinical_text_sources_for_chunking,
)


def main():
    # Retrieve records from all selected clinical tables.
    records = get_all_clinical_text_sources_for_chunking()

    assert isinstance(records, list)

    # Count records by their source table.
    source_counts = Counter(record["source_table"] for record in records)

    print("Total clinical text records:", len(records))
    print("\nRecords by source table:")

    expected_tables = [
        "clinical_content",
        "consultation_history",
        "consultation_diagnosis",
        "consultation_investigations",
        "consultation_medications",
        "consultation_procedures",
    ]

    for table in expected_tables:
        print(f"{table}: {source_counts.get(table, 0)}")

    # Verify the structure without displaying clinical text.
    required_fields = {
        "source_record_id",
        "consultation_id",
        "source_table",
        "section_name",
        "content_text",
    }

    for record in records:
        assert required_fields.issubset(record.keys())
        assert record["source_record_id"]
        assert record["content_text"].strip()

    print("\nRecord structure verified.")
    print("No empty text records returned.")
    print("All clinical text source tests passed!")


if __name__ == "__main__":
    main()
