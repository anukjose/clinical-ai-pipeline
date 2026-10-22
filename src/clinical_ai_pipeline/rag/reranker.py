"""Rerank retrieved clinical chunks using lexical and source relevance."""

import re
from collections import Counter
from typing import Any

# Common words that usually contribute little to clinical relevance.
STOP_WORDS = {
    "a",
    "an",
    "and",
    "find",
    "for",
    "in",
    "information",
    "of",
    "on",
    "the",
    "to",
    "what",
    "with",
}


def tokenize(text: str) -> list[str]:
    """Convert text into lowercase alphanumeric word tokens."""
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def rerank_chunks(
    query: str,
    chunks: list[Any],
    limit: int = 5,
) -> list[Any]:
    """Rank candidate chunks by query-term overlap and source relevance.

    This lightweight baseline is not a clinical relevance model.
    Original order is preserved when scores are tied.
    """
    if not query.strip():
        raise ValueError("Query must not be empty.")

    if limit < 1:
        raise ValueError("Limit must be at least 1.")

    query_terms = set(tokenize(query)) - STOP_WORDS

    if not query_terms or not chunks:
        return chunks[:limit]

    query_mentions_medication = bool(
        {"medication", "medications", "drug", "drugs"} & query_terms
    )

    scored_chunks = []

    for original_position, chunk in enumerate(chunks):
        chunk_text = getattr(chunk, "chunk_text", "")
        chunk_terms = Counter(tokenize(chunk_text))

        matched_terms = query_terms.intersection(chunk_terms.keys())
        lexical_score = len(matched_terms) / len(query_terms)

        # Give a small bonus only when the query explicitly concerns
        # medication and the candidate comes from the medication table.
        source_table = getattr(chunk, "source_table", None)
        source_bonus = (
            0.15
            if query_mentions_medication and source_table == "consultation_medications"
            else 0.0
        )

        final_score = lexical_score + source_bonus

        scored_chunks.append((final_score, original_position, chunk))

    # Higher scores first; preserve original order when scores tie.
    scored_chunks.sort(key=lambda item: (-item[0], item[1]))

    return [chunk for _, _, chunk in scored_chunks[:limit]]
