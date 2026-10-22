"""
Clinical text chunking module.

Splits clinical text into smaller, overlapping chunks
while preserving the source and consultation metadata.
"""

from typing import Any


def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 60,
) -> list[str]:
    """
    Split text into chunks using words as an initial approximation
    of tokens.

    Short text is kept as a single chunk.
    Longer text is split with overlap to preserve context.

    Args:
        text: Clinical text to split.
        chunk_size: Maximum approximate number of words per chunk.
        overlap: Number of words repeated between consecutive chunks.

    Returns:
        A list of text chunks.
    """

    # Reject invalid chunking settings.
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and less than chunk_size")

    # Handle missing or whitespace-only text.
    if not text or not text.strip():
        return []

    # Split the text into words.
    words = text.split()

    # Keep short text intact.
    if len(words) <= chunk_size:
        return [" ".join(words)]

    chunks = []
    start = 0

    while start < len(words):
        # Calculate the end of the current chunk.
        end = start + chunk_size

        # Join the selected words into one chunk.
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        # Stop once we have reached the end of the text.
        if end >= len(words):
            break

        # Move forward while retaining some words from
        # the previous chunk to preserve context.
        start = end - overlap

    return chunks


def create_clinical_chunks(
    text: str,
    consultation_id: int,
    source_table: str,
    source_record_id: str,
    section_name: str,
    chunk_size: int = 400,
    overlap: int = 60,
) -> list[dict[str, Any]]:
    """
    Create source-aware chunks ready for database persistence.

    Each chunk retains enough metadata to trace it back to
    its original clinical record.
    """

    # Split the supplied text into smaller pieces.
    text_chunks = chunk_text(
        text=text,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    clinical_chunks = []

    for index, chunk in enumerate(text_chunks):
        clinical_chunks.append(
            {
                "consultation_id": consultation_id,
                "source_table": source_table,
                "source_record_id": source_record_id,
                "section_name": section_name,
                "chunk_text": chunk,
                "chunk_index": index,
            }
        )

    return clinical_chunks
