"""
Test chunking clinical text retrieved from all selected tables.
"""

from collections import Counter

from clinical_ai_pipeline.processing.chunker import (
    create_clinical_chunks,
)
from clinical_ai_pipeline.storage.postgres_repository import (
    get_all_clinical_text_sources_for_chunking,
)


def main():
    # Step 1: Retrieve all searchable clinical text.
    records = get_all_clinical_text_sources_for_chunking()

    # Step 2: Chunk each record while preserving its source metadata.
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

    # Step 3: Count the generated chunks by source table.
    chunk_counts = Counter(chunk["source_table"] for chunk in all_chunks)

    print("Source records retrieved:", len(records))
    print("Total chunks created:", len(all_chunks))
    print("\nChunks by source table:")

    for table in sorted(chunk_counts):
        print(f"{table}: {chunk_counts[table]}")

    # Step 4: Validate the generated chunks.
    required_fields = {
        "consultation_id",
        "source_table",
        "source_record_id",
        "section_name",
        "chunk_text",
        "chunk_index",
    }

    for chunk in all_chunks:
        assert required_fields.issubset(chunk.keys())
        assert chunk["chunk_text"].strip()
        assert chunk["source_record_id"]
        assert chunk["chunk_index"] >= 0

    print("\nChunk structure verified.")
    print("Source metadata preserved.")
    print("No empty chunks created.")
    print("All clinical chunking tests passed!")


if __name__ == "__main__":
    main()
