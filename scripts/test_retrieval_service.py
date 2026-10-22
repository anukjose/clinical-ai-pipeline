"""Integration test for the clinical retrieval service."""

from clinical_ai_pipeline.retrieval.models import RetrievalRequest
from clinical_ai_pipeline.retrieval.service import RetrievalService


def main() -> None:
    """Compare unrestricted and source-filtered clinical retrieval."""

    retrieval_service = RetrievalService()

    test_cases = [
        {
            "name": "Unrestricted semantic search",
            "request": RetrievalRequest(
                query="Find medication dosage and frequency information",
                limit=5,
            ),
        },
        {
            "name": "Medication-only search",
            "request": RetrievalRequest(
                query="Find medication dosage and frequency information",
                source_table="consultation_medications",
                limit=5,
            ),
        },
    ]

    for test_case in test_cases:
        response = retrieval_service.search(test_case["request"])

        print(f"\n{test_case['name']}")
        print("=" * 60)
        print("Query:", response.query)
        print("Results found:", response.result_count)

        for index, chunk in enumerate(response.results, start=1):
            print(
                f"Result {index}: "
                f"source={chunk.source_table}, "
                f"distance={chunk.cosine_distance:.4f}"
            )

        # Confirm every returned result respects the source filter.
        requested_source = test_case["request"].source_table

        if requested_source is not None:
            assert all(
                chunk.source_table == requested_source for chunk in response.results
            ), "A result does not match the requested source filter."

            print("Source filter check: PASSED")


if __name__ == "__main__":
    main()
