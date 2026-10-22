
"""
Normalization component for the Clinical AI Pipeline.

Responsibilities:
1. Convert a validated MedicationRecord into a consistent dictionary.
2. Use snake_case field names.
3. Preserve the original clinical values.
4. Normalize prescription section metadata.
5. Prepare the record for future storage and processing.

This module does not:
- Read files from S3.
- Validate the original input structure.
- Modify clinical meaning.
- Call an LLM or generate embeddings.
"""

from typing import Any

from clinical_ai_pipeline.processing.models import MedicationRecord
from clinical_ai_pipeline.utils.logging_config import get_app_logger


# Create a module-specific logger.
logger = get_app_logger(__name__)


def normalize_medication_record(
    record: MedicationRecord,
) -> dict[str, Any]:
    """
    Convert a validated MedicationRecord into a normalized dictionary.

    Args:
        record: A validated MedicationRecord Pydantic object.

    Returns:
        A dictionary with consistent snake_case field names.

    Notes:
        Clinical values are preserved.
        This function changes the representation, not the meaning.
    """

    logger.info(
        "Starting medication record normalization | medication_id=%s",
        record.medicationId,
    )

    # Convert the validated Pydantic model into a dictionary.
    # This provides a convenient structure for field transformation.
    record_data = record.model_dump()

    # Normalize the main record fields.
    normalized_record: dict[str, Any] = {
        "medication_id": record_data["medicationId"],
        "consultation_date": record_data["consultationDate"],
        "medication_status": record_data["medicationStatus"],
        "doctor": {
            "employee_id": record_data["doctor"]["employeeId"],
            "department_name": record_data["doctor"]["departmentName"],
        },
        "patient": {
            "customer_id": record_data["patient"]["customerId"],
            "date_of_birth": record_data["patient"]["customerDob"],
            "gender": record_data["patient"]["gender"],
        },
        "next_review": record_data["nextReview"],
        "prescription": [],
    }

    # Normalize each prescription section.
    #
    # The nested 'data' fields vary between section types.
    # Therefore, we normalize the section metadata while preserving
    # the original nested data without forcing an incorrect structure.
    for section in record_data["prescription"]:
        normalized_section = {
            "section_id": section["sectionId"],
            "section_name": section["sectionName"],
            "section_type": section["type"],
            "section_type_label": section["typeLabel"],
            "data": section["data"],
        }

        normalized_record["prescription"].append(
            normalized_section
        )

    logger.info(
        "Medication record normalization successful | medication_id=%s",
        record.medicationId,
    )

    # Return the normalized dictionary for the next pipeline stage.
    return normalized_record