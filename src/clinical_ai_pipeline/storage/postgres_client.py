
"""
PostgreSQL connection module for the Clinical AI Pipeline.
"""

import psycopg

from clinical_ai_pipeline.config.settings import settings
from clinical_ai_pipeline.utils.logging_config import get_app_logger

logger = get_app_logger(__name__)


def get_postgres_connection():
    """
    Create and return a PostgreSQL database connection.
    """

    try:
        connection = psycopg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_database,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )

        logger.info(
            "Successfully connected to PostgreSQL database: %s",
            settings.postgres_database,
        )

        return connection

    except psycopg.Error as error:
        logger.exception(
            "Failed to connect to PostgreSQL database: %s",
            settings.postgres_database,
        )

        raise RuntimeError(
            "Unable to connect to PostgreSQL database"
        ) from error