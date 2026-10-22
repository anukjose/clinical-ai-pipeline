
"""
Custom exceptions for the Clinical AI Pipeline.

These exceptions provide meaningful error categories
that can be handled consistently across the application.
"""


class ClinicalAIPipelineError(Exception):
    """
    Base exception for all application-specific errors.

    Other custom exceptions inherit from this class.
    """

    pass


class S3StorageError(ClinicalAIPipelineError):
    """
    Raised when an S3 storage operation fails.

    Examples:
    - Unable to read an S3 object.
    - AWS permission failure.
    - S3 connection issue.
    """

    pass


class DataValidationError(ClinicalAIPipelineError):
    """
    Raised when input data fails validation.

    Examples:
    - Missing required fields.
    - Incorrect data types.
    - Invalid record structure.
    """

    pass


class IngestionError(ClinicalAIPipelineError):
    """
    Raised when the ingestion workflow fails.

    Used for broader ingestion-related errors
    that do not belong to a more specific category.
    """

    pass