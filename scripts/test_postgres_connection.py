"""
Test PostgreSQL database connectivity.
"""

from clinical_ai_pipeline.storage.postgres_client import (
    get_postgres_connection,
)
from clinical_ai_pipeline.utils.logging_config import (
    configure_logging,
)


def main():
    configure_logging()

    connection = None

    try:
        # Open a connection using our application settings.
        connection = get_postgres_connection()

        # Verify that the connection is active.
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

        print("PostgreSQL connection successful!")
        print("Test query result:", result)

    finally:
        # Close the connection after testing.
        if connection is not None:
            connection.close()
            print("PostgreSQL connection closed.")


if __name__ == "__main__":
    main()
