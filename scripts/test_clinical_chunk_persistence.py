"""
Test retrieving, chunking and saving clinical chunks.
"""

from collections import Counter

from clinical_ai_pipeline.processing.chunker import (
    create_clinical_chunks,
)
from clinical_ai_pipeline.storage.postgres_repository import (
    get_all_clinical_text_sources_for_chunking,
    save_clinical_chunks,
)


def main():
    # Step 1: Retrieve clinical text.
    records = get_all_clinical_text_sources_for_chunking()

    # Step 2: Create chunks from all retrieved records.
    all_chunks = []

    for record in records:
        chunks = create_clinical_chunks(
            text=record["content_text"],
            consultation_id=record["consultation_id"],
            source_table=record["source_table"],
            source_record_id=record["source_record_id"],
            section_name=record["section_name"],
        )

        all_chunks.extend(chunks)

    # Step 3: Save the chunks to PostgreSQL.
    saved_count = save_clinical_chunks(all_chunks)

    # Report counts without printing clinical text.
    counts_by_source = Counter(chunk["source_table"] for chunk in all_chunks)

    print("Source records retrieved:", len(records))
    print("Chunks generated:", len(all_chunks))
    print("Chunks processed for saving:", saved_count)
    print("\nChunks by source table:")

    for table, count in sorted(counts_by_source.items()):
        print(f"{table}: {count}")

    print("\nClinical chunk persistence test completed.")


if __name__ == "__main__":
    main()
