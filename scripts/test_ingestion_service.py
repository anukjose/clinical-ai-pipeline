
"""
Test script for the ingestion service.

Runs the ingestion workflow and prints
a summary of the results.
"""

from clinical_ai_pipeline.ingestion.service import (
    run_ingestion,
    summarize_ingestion,
)
from clinical_ai_pipeline.utils.logging_config import (
    configure_logging,
)


def main():
    configure_logging()

    # Run ingestion for all medication files in S3.
    results = run_ingestion()

    # Generate summary counts.
    summary = summarize_ingestion(results)

    print("\n===== INGESTION SUMMARY =====")
    print("Total processed:", summary["total_processed"])
    print("Success:", summary["success"])
    print("Failed:", summary["failed"])
    print("Quarantined:", summary["quarantined"])
    print("=============================")


if __name__ == "__main__":
    main()