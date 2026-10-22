"""Manually test hybrid retrieval and grounded answer generation."""

from clinical_ai_pipeline.rag.models import RAGRequest
from clinical_ai_pipeline.rag.service import RAGService


def main() -> None:
    service = RAGService()

    request = RAGRequest(
        question=(
            "What medication dosage and frequency are explicitly "
            "recorded in the available evidence?"
        ),
        retrieval_limit=5,
    )

    response = service.answer(request)

    print(f"Question: {response.question}")
    print(f"Insufficient evidence: {response.insufficient_evidence}")
    print(f"Evidence count: {len(response.evidence)}")
    print(f"\nAnswer:\n{response.answer}")

    print("\nEvidence references:")
    for index, evidence in enumerate(response.evidence, start=1):
        print(f"\nEvidence {index}")
        print(f"Source table: {evidence.source_table}")
        print(f"Section: {evidence.section_name}")
        print(f"Score: {evidence.similarity_score:.6f}")
        print(f"Text preview: {evidence.chunk_text[:150]}")


if __name__ == "__main__":
    main()
