"""
Test the clinical text chunking module.
"""

from clinical_ai_pipeline.processing.chunker import (
    chunk_text,
    create_clinical_chunks,
)


def main():
    # Test 1: A short clinical note should remain one chunk.
    short_text = "Patient reports a headache and mild nausea."

    short_chunks = chunk_text(short_text)

    assert len(short_chunks) == 1
    print("Test 1 passed: Short text remains one chunk.")

    # Test 2: Empty text should produce no chunks.
    empty_chunks = chunk_text("   ")

    assert empty_chunks == []
    print("Test 2 passed: Empty text produces no chunks.")

    # Test 3: Long text should be split with overlap.
    long_text = " ".join(f"word{i}" for i in range(950))

    long_chunks = chunk_text(
        text=long_text,
        chunk_size=400,
        overlap=60,
    )

    assert len(long_chunks) == 3
    assert len(long_chunks[0].split()) == 400
    assert len(long_chunks[1].split()) == 400
    assert len(long_chunks[2].split()) == 270

    print("Test 3 passed: Long text is split correctly.")

    # Test 4: Verify that source metadata is retained.
    clinical_chunks = create_clinical_chunks(
        text=short_text,
        consultation_id=169584,
        source_table="clinical_content",
        source_record_id="test-record-id",
        section_name="Chief Complaint",
    )

    assert len(clinical_chunks) == 1
    assert clinical_chunks[0]["consultation_id"] == 169584
    assert clinical_chunks[0]["source_table"] == "clinical_content"
    assert clinical_chunks[0]["section_name"] == "Chief Complaint"

    print("Test 4 passed: Chunk metadata is preserved.")

    print("\nAll chunker tests passed!")


if __name__ == "__main__":
    main()
