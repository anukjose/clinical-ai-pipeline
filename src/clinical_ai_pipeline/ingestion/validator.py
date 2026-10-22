
"""
Validation component for the Clinical AI Pipeline.

Responsibilities:
1. Validate S3 JSON data using the MedicationRecord model.
2. Return a strongly typed MedicationRecord object.
3. Log validation failures without exposing clinical information.
4. Convert Pydantic validation errors into application-specific errors.

This module does not read files from S3.
Reading is handled by the reader component.
"""

from typing import Any

from pydantic import ValidationError

from clinical_ai_pipeline.processing.models import MedicationRecord
from clinical_ai_pipeline.utils.exceptions import DataValidationError
from clinical_ai_pipeline.utils.logging_config import get_app_logger


# Create a module-specific logger.
# The central logging configuration controls its output format.
logger = get_app_logger(__name__)


def validate_medication_record(
    data: dict[str, Any],
) -> MedicationRecord:
    """
    Validate a dictionary against the MedicationRecord model.

    Args:
        data: JSON data converted into a Python dictionary.

    Returns:
        A validated MedicationRecord Pydantic object.

    Raises:
        DataValidationError:
            If the data does not match the expected model structure.
    """

    logger.info("Starting medication record validation")

    try:
        # Pydantic validates the dictionary against the model,
        # including required fields and nested model structures.
        validated_record = MedicationRecord.model_validate(data)

        logger.info(
            "Medication record validation successful"
        )

        # Return the validated and strongly typed object.
        return validated_record

    except ValidationError as error:
        # Log the error details for developers.
        # Do not log the complete input because it may contain
        # patient information or clinical notes.
        logger.error(
            "Medication record validation failed | error_type=%s",
            type(error).__name__,
        )

        # Convert the Pydantic error into our application-specific
        # validation exception.
        raise DataValidationError(
            "Medication record failed validation"
        ) from error