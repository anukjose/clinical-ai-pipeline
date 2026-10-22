"""Manually test PostgreSQL clinical keyword search."""

from clinical_ai_pipeline.storage.postgres_repository import (
    search_keyword_clinical_chunks,
)


def main() -> None:
    # Use the same query we have been investigating.
    query = "Find medication dosage and frequency information"

    results = search_keyword_clinical_chunks(
        query=query,
        limit=10,
    )

    print(f"Query: {query}")
    print(f"Number of results: {len(results)}")

    # Print ranking and source metadata only.
    # Do not print clinical text or patient information.
    for index, result in enumerate(results, start=1):
        print(
            f"{index}. "
            f"source_table={result.get('source_table')}, "
            f"keyword_rank={result.get('keyword_rank')}"
        )


if __name__ == "__main__":
    main()
