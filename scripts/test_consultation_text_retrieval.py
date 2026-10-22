"""Test clinical text retrieval for one consultation."""

from collections import Counter

from clinical_ai_pipeline.storage.postgres_repository import (
    get_all_clinical_text_sources_for_chunking,
)


def main() -> None:
    # Retrieve text only for the consultation under test.
    consultation_id = 169584

    records = get_all_clinical_text_sources_for_chunking(
        consultation_id=consultation_id
    )

    # Display counts and metadata, never the actual clinical text.
    source_counts = Counter(record["source_table"] for record in records)

    print("Consultation ID:", consultation_id)
    print("Text sources retrieved:", len(records))
    print("Sources by table:", dict(source_counts))

    # Ensure no other consultation was returned.
    assert all(
        record["consultation_id"] == consultation_id for record in records
    ), "Unexpected consultation ID returned!"

    print("Consultation filter test passed.")


if __name__ == "__main__":
    main()
