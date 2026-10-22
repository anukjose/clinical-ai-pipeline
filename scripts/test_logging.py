import logging

from clinical_ai_pipeline.utils.logging_config import (
    configure_logging,
    get_app_logger,
)


configure_logging()

logger = get_app_logger(__name__)

logger.info("Logging test started")
logger.warning("This is a warning message")
logger.error("This is an error message")