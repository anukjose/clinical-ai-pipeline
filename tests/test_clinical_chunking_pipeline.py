"""
Test retrieving clinical content and converting it into chunks.
"""

from clinical_ai_pipeline.processing.chunker import (
    create_clinical_chunks,
)
from clinical_ai_pipeline.storage.postgres_repository import (
    get_clinical_content_for_chunking,
)


def main():
    # Step 1: Retrieve clinical content from PostgreSQL.
    records = get_clinical_content_for_chunking()

    all_chunks = []

    # Step 2: Convert each retrieved record into chunks.
    for record in records:
        chunks = create_clinical_chunks(
            text=record["content_text"],
            consultation_id=record["consultation_id"],
            source_table=record["source_table"],
            source_record_id=record["source_record_id"],
            section_name=record["section_name"],
        )

        all_chunks.extend(chunks)

    # Step 3: Verify the results without printing clinical text.
    print("Clinical records retrieved:", len(records))
    print("Total chunks created:", len(all_chunks))

    if all_chunks:
        required_fields = {
            "consultation_id",
            "source_table",
            "source_record_id",
            "section_name",
            "chunk_text",
            "chunk_index",
        }

        assert required_fields.issubset(all_chunks[0].keys())
        assert all(chunk["chunk_text"].strip() for chunk in all_chunks)

        print("Chunk structure verified.")
        print("Source metadata preserved.")
        print("No empty chunks created.")
    else:
        print("No chunks were created from the retrieved records.")

    print("Clinical chunking pipeline test completed.")


if __name__ == "__main__":
    main()
