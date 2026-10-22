"""
PostgreSQL repository for the Clinical AI Pipeline.

Responsibilities:
1. Insert or retrieve patients.
2. Insert consultations.
3. Maintain relationships between patients and consultations.

This module does not read files from S3.
"""

from typing import Any
from psycopg.types.json import Jsonb
from pgvector.psycopg import register_vector
from pgvector import Vector

from clinical_ai_pipeline.storage.postgres_client import (
    get_postgres_connection,
)
from clinical_ai_pipeline.utils.logging_config import get_app_logger

logger = get_app_logger(__name__)


def save_patient_and_consultation(
    normalized_record: dict[str, Any],
) -> None:
    """
    Save a patient and their consultation in PostgreSQL.

    The patient is identified using the original customer_id.
    The consultation is identified using medication_id.
    """

    connection = None

    try:
        connection = get_postgres_connection()

        with connection.cursor() as cursor:

            # Insert the patient if they do not already exist.
            # Return the internal UUID for relationship mapping.
            cursor.execute(
                """
                INSERT INTO patients (
                    customer_id,
                    date_of_birth,
                    gender
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (customer_id)
                DO UPDATE SET
                    date_of_birth = EXCLUDED.date_of_birth,
                    gender = EXCLUDED.gender
                RETURNING patient_id;
                """,
                (
                    normalized_record["patient"]["customer_id"],
                    normalized_record["patient"]["date_of_birth"],
                    normalized_record["patient"]["gender"],
                ),
            )

            patient_id = cursor.fetchone()[0]

            # Insert the consultation using medication_id
            # as the consultation identifier.
            cursor.execute(
                """
                INSERT INTO consultations (
                    consultation_id,
                    patient_id,
                    consultation_date,
                    medication_status
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (consultation_id)
                DO UPDATE SET
                    patient_id = EXCLUDED.patient_id,
                    consultation_date = EXCLUDED.consultation_date,
                    medication_status = EXCLUDED.medication_status;
                """,
                (
                    normalized_record["medication_id"],
                    patient_id,
                    normalized_record["consultation_date"],
                    normalized_record["medication_status"],
                ),
            )

        # Commit both operations as one transaction.
        connection.commit()

        logger.info(
            "Patient and consultation saved | consultation_id=%s",
            normalized_record["medication_id"],
        )

    except Exception as error:
        # Roll back both operations if anything fails.
        if connection is not None:
            connection.rollback()

        logger.exception("Failed to save patient and consultation")

        raise RuntimeError("Unable to save patient and consultation") from error

    finally:
        # Always close the database connection.
        if connection is not None:
            connection.close()


def _get_section_data(
    normalized_record: dict[str, Any],
    section_name: str,
) -> list[dict[str, Any]]:
    """Return the items for a named prescription section."""
    for section in normalized_record["prescription"]:
        if section["section_name"] == section_name:
            return section["data"] or []
    return []


def _replace_consultation_rows(
    table_name: str,
    consultation_id: int,
    insert_query: str,
    rows: list[tuple],
) -> None:
    """Atomically replace derived rows for one consultation in one table."""
    allowed_tables = {
        "consultation_vitals",
        "consultation_medications",
        "consultation_history",
        "consultation_investigations",
        "consultation_procedures",
    }
    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table: {table_name}")

    connection = None
    try:
        connection = get_postgres_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {table_name} WHERE consultation_id = %s",
                (consultation_id,),
            )
            if rows:
                cursor.executemany(insert_query, rows)
        connection.commit()
        logger.info(
            "Consultation rows replaced | table=%s | consultation_id=%s | count=%s",
            table_name,
            consultation_id,
            len(rows),
        )
    except Exception as error:
        if connection is not None:
            connection.rollback()
        logger.exception("Failed to replace consultation rows | table=%s", table_name)
        raise RuntimeError(f"Unable to replace rows in {table_name}") from error
    finally:
        if connection is not None:
            connection.close()


def save_consultation_vitals(
    normalized_record: dict[str, Any],
) -> None:
    """Replace vital records for a consultation."""
    consultation_id = normalized_record["medication_id"]
    vitals = _get_section_data(normalized_record, "Vitals")
    query = """
        INSERT INTO consultation_vitals (
            consultation_id, label,
            value_1, unit_1, value_2, unit_2,
            value_3, unit_3, value_4, unit_4
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    rows = [
        (
            consultation_id,
            vital.get("label"),
            vital.get("val1"),
            vital.get("unit1"),
            vital.get("val2"),
            vital.get("unit2"),
            vital.get("val3"),
            vital.get("unit3"),
            vital.get("val4"),
            vital.get("unit4"),
        )
        for vital in vitals
    ]
    _replace_consultation_rows("consultation_vitals", consultation_id, query, rows)


def save_consultation_medications(
    normalized_record: dict[str, Any],
) -> None:
    """Replace medication records for a consultation."""
    consultation_id = normalized_record["medication_id"]
    medicines = _get_section_data(normalized_record, "Medicine")
    query = """
        INSERT INTO consultation_medications (
            consultation_id, item_id, item_name, dose, dose_unit,
            frequency, duration, duration_unit, quantity, note
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    rows = [
        (
            consultation_id,
            medicine.get("itemId"),
            medicine.get("itemName"),
            medicine.get("medprescDose"),
            medicine.get("doseUnit"),
            medicine.get("medprescFrequency"),
            medicine.get("medprescDuration"),
            medicine.get("durationUnit"),
            medicine.get("medprescQty"),
            medicine.get("medprescNote"),
        )
        for medicine in medicines
    ]
    _replace_consultation_rows("consultation_medications", consultation_id, query, rows)


def save_next_review(
    normalized_record: dict[str, Any],
) -> None:
    """
    Save the consultation's next review information.
    """

    connection = None

    try:
        connection = get_postgres_connection()

        consultation_id = normalized_record["medication_id"]

        # Find the Next Review section.
        review_data = []

        for section in normalized_record["prescription"]:
            if section["section_name"] == "Next Review":
                review_data = section["data"]
                break

        # If no review information exists, do nothing.
        if not review_data:
            logger.info(
                "No next review found | consultation_id=%s",
                consultation_id,
            )
            return

        review = review_data[0]

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO next_reviews (
    consultation_id,
    review_date,
    review_condition,
    schedule_type_id
)
VALUES (%s, %s, %s, %s)
ON CONFLICT (consultation_id)
DO UPDATE SET
    review_date = EXCLUDED.review_date,
    review_condition = EXCLUDED.review_condition,
    schedule_type_id = EXCLUDED.schedule_type_id;
                """,
                (
                    consultation_id,
                    review.get("date"),
                    review.get("reviewCondition"),
                    review.get("scheduletypeId"),
                ),
            )

        connection.commit()

        logger.info(
            "Next review saved | consultation_id=%s",
            consultation_id,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        logger.exception("Failed to save next review")

        raise RuntimeError("Unable to save next review") from error

    finally:
        if connection is not None:
            connection.close()


def save_consultation_history(
    normalized_record: dict[str, Any],
) -> None:
    """Replace history records for a consultation."""
    consultation_id = normalized_record["medication_id"]
    history_items = _get_section_data(normalized_record, "History")
    query = """
        INSERT INTO consultation_history (
            consultation_id, history_text, source
        )
        VALUES (%s, %s, %s);
    """
    rows = [(consultation_id, item.get("text"), "History") for item in history_items]
    _replace_consultation_rows("consultation_history", consultation_id, query, rows)


def save_consultation_investigations(
    normalized_record: dict[str, Any],
) -> None:
    """Replace investigation records for a consultation."""
    consultation_id = normalized_record["medication_id"]
    investigations = _get_section_data(normalized_record, "Investigation")
    query = """
        INSERT INTO consultation_investigations (
            consultation_id, investigation_date, investigation_name,
            investigation_code, result, note
        )
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    rows = [
        (
            consultation_id,
            item.get("date"),
            item.get("name"),
            str(item["id"]) if item.get("id") is not None else None,
            item.get("result"),
            item.get("note"),
        )
        for item in investigations
    ]
    _replace_consultation_rows(
        "consultation_investigations", consultation_id, query, rows
    )


def save_consultation_procedures(
    normalized_record: dict[str, Any],
) -> None:
    """Replace procedure records for a consultation."""
    consultation_id = normalized_record["medication_id"]
    procedures = _get_section_data(normalized_record, "Procedure")
    query = """
        INSERT INTO consultation_procedures (
            consultation_id, procedure_date, procedure_name,
            procedure_code, note
        )
        VALUES (%s, %s, %s, %s, %s);
    """
    rows = [
        (
            consultation_id,
            item.get("date"),
            item.get("name"),
            str(item["id"]) if item.get("id") is not None else None,
            item.get("note"),
        )
        for item in procedures
    ]
    _replace_consultation_rows("consultation_procedures", consultation_id, query, rows)


def save_clinical_content(
    normalized_record: dict[str, Any],
) -> None:
    """
    Save selected clinical content sections for a consultation.

    Each clinical section is stored as one database row.
    """
    # Define the clinical sections to save in clinical_content.
    content_section_names = {
        "Chief Complaint",
        "Examination",
        "Diagnosis",
        "Plan of Care",
        "Other Notes",
        "Nursing Note",
    }

    connection = None

    try:
        connection = get_postgres_connection()

        consultation_id = normalized_record["medication_id"]

        for section in normalized_record["prescription"]:
            if section["section_name"] in content_section_names:
                # Get the section name.
                section_name = section["section_name"]

                # Get the original data list.
                content_data = section["data"]

                # Extract text from each item.
                content_text = "\n".join(
                    item.get("text", "") for item in content_data if item.get("text")
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                    INSERT INTO clinical_content (
                        consultation_id,
                        section_name,
                        content_text,
                        content_data
                        )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (consultation_id, section_name)
                    DO UPDATE SET
                    content_text = EXCLUDED.content_text,
                    content_data = EXCLUDED.content_data;
                    """,
                        (
                            consultation_id,
                            section_name,
                            content_text,
                            Jsonb(content_data),
                        ),
                    )

        connection.commit()

        logger.info(
            "Clinical content saved | consultation_id=%s",
            consultation_id,
        )

    except Exception as error:
        if connection is not None:
            connection.rollback()

        logger.exception("Failed to save clinical content")

        raise RuntimeError("Unable to save clinical content") from error
    finally:
        if connection is not None:
            connection.close()


def get_clinical_content_for_chunking() -> list[dict[str, Any]]:
    """
    Retrieve clinical content from PostgreSQL for chunking.
    Returns the source identifiers and text required to
    create traceable clinical chunks.
    """
    connection = None
    try:
        connection = get_postgres_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    content_id,
                    consultation_id,
                    section_name,
                    content_text
                FROM clinical_content
                WHERE content_text IS NOT NULL
                  AND TRIM(content_text) <> ''
                ORDER BY consultation_id, section_name;
                """)
            rows = cursor.fetchall()
        # Convert database rows into dictionaries.
        records = [
            {
                "source_record_id": str(row[0]),
                "consultation_id": row[1],
                "section_name": row[2],
                "content_text": row[3],
                "source_table": "clinical_content",
            }
            for row in rows
        ]
        logger.info(
            "Retrieved clinical content for chunking | count=%s",
            len(records),
        )
        return records
    except Exception as error:
        logger.exception("Failed to retrieve clinical content for chunking")
        raise RuntimeError(
            "Unable to retrieve clinical content for chunking"
        ) from error
    finally:
        if connection is not None:
            connection.close()


def get_all_clinical_text_sources_for_chunking(
    consultation_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve searchable text from the selected clinical tables.

    If consultation_id is provided, retrieve text only for that
    consultation. Otherwise, retrieve text from all consultations.

    Each result contains:
        - source_record_id
        - consultation_id
        - source_table
        - section_name
        - content_text
    """
    connection = None

    # Combine searchable text from all selected clinical tables.
    # The outer query applies an optional filter to every source.
    query = """
        SELECT
            content_id AS source_record_id,
            consultation_id,
            'clinical_content' AS source_table,
            section_name,
            content_text
        FROM clinical_content
        WHERE content_text IS NOT NULL
          AND TRIM(content_text) <> ''

        UNION ALL

        SELECT
            history_id AS source_record_id,
            consultation_id,
            'consultation_history' AS source_table,
            'History' AS section_name,
            history_text AS content_text
        FROM consultation_history
        WHERE history_text IS NOT NULL
          AND TRIM(history_text) <> ''

        UNION ALL

        SELECT
            diagnosis_id AS source_record_id,
            consultation_id,
            'consultation_diagnosis' AS source_table,
            'Diagnosis' AS section_name,
            CONCAT_WS(
                ' | ',
                NULLIF(TRIM(diagnosis_text), ''),
                CASE
                    WHEN diagnosis_code IS NOT NULL
                    THEN 'Code: ' || diagnosis_code
                END,
                NULLIF(TRIM(diagnosis_type), ''),
                NULLIF(TRIM(note), '')
            ) AS content_text
        FROM consultation_diagnosis

        UNION ALL

        SELECT
            investigation_id AS source_record_id,
            consultation_id,
            'consultation_investigations' AS source_table,
            'Investigation' AS section_name,
            CONCAT_WS(
                ' | ',
                NULLIF(TRIM(investigation_name), ''),
                CASE
                    WHEN investigation_date IS NOT NULL
                    THEN 'Date: ' || investigation_date::text
                END,
                CASE
                    WHEN investigation_code IS NOT NULL
                    THEN 'Code: ' || investigation_code
                END,
                NULLIF(TRIM(result), ''),
                NULLIF(TRIM(note), '')
            ) AS content_text
        FROM consultation_investigations

        UNION ALL

        SELECT
            medication_record_id AS source_record_id,
            consultation_id,
            'consultation_medications' AS source_table,
            'Medication' AS section_name,
            CONCAT_WS(
                ' | ',
                NULLIF(TRIM(item_name), ''),
                CASE
                    WHEN dose IS NOT NULL
                    THEN 'Dose: ' || dose::text
                END,
                NULLIF(TRIM(dose_unit), ''),
                CASE
                    WHEN frequency IS NOT NULL
                    THEN 'Frequency: ' || frequency::text
                END,
                CASE
                    WHEN duration IS NOT NULL
                    THEN 'Duration: ' || duration::text
                END,
                NULLIF(TRIM(duration_unit), ''),
                CASE
                    WHEN quantity IS NOT NULL
                    THEN 'Quantity: ' || quantity::text
                END,
                NULLIF(TRIM(note), '')
            ) AS content_text
        FROM consultation_medications

        UNION ALL

        SELECT
            procedure_id AS source_record_id,
            consultation_id,
            'consultation_procedures' AS source_table,
            'Procedure' AS section_name,
            CONCAT_WS(
                ' | ',
                NULLIF(TRIM(procedure_name), ''),
                CASE
                    WHEN procedure_date IS NOT NULL
                    THEN 'Date: ' || procedure_date::text
                END,
                CASE
                    WHEN procedure_code IS NOT NULL
                    THEN 'Code: ' || procedure_code
                END,
                NULLIF(TRIM(note), '')
            ) AS content_text
        FROM consultation_procedures
    """

    # Apply one filter to the combined results, rather than repeating
    # the consultation condition in every UNION ALL branch.
    if consultation_id is not None:
        query = f"""
            SELECT *
            FROM (
                {query}
            ) AS clinical_text_sources
            WHERE consultation_id = %s
            ORDER BY consultation_id, source_table, section_name
        """
    else:
        query += """
            ORDER BY consultation_id, source_table, section_name
        """

    try:
        connection = get_postgres_connection()

        with connection.cursor() as cursor:
            # Parameterisation keeps the consultation ID separate
            # from the SQL query.
            if consultation_id is not None:
                cursor.execute(query, (consultation_id,))
            else:
                cursor.execute(query)

            rows = cursor.fetchall()

        # Convert database rows into dictionaries used by the chunker.
        records = [
            {
                "source_record_id": str(row[0]),
                "consultation_id": row[1],
                "source_table": row[2],
                "section_name": row[3],
                "content_text": row[4],
            }
            for row in rows
            if row[4] and row[4].strip()
        ]

        logger.info(
            "Retrieved clinical text sources for chunking | "
            "consultation_id=%s | count=%s",
            consultation_id,
            len(records),
        )

        return records

    except Exception as error:
        logger.exception("Failed to retrieve clinical text sources for chunking")
        raise RuntimeError(
            "Unable to retrieve clinical text sources for chunking"
        ) from error

    finally:
        if connection is not None:
            connection.close()


def save_clinical_chunks(
    chunks: list[dict[str, Any]],
) -> int:
    """
    Replace existing chunks for the consultations being processed.

    Existing chunks from the selected clinical source tables are deleted
    and rebuilt in one transaction. This prevents old chunks from
    accumulating when source-record UUIDs change during ingestion.

    Returns:
        The number of chunks inserted.
    """
    if not chunks:
        logger.info("No clinical chunks to save.")
        return 0

    connection = None

    insert_query = """
        INSERT INTO clinical_chunks (
            consultation_id,
            source_table,
            source_record_id,
            section_name,
            chunk_text,
            chunk_index
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_table, source_record_id, chunk_index)
        DO UPDATE SET
            consultation_id = EXCLUDED.consultation_id,
            section_name = EXCLUDED.section_name,
            embedding = CASE
        WHEN clinical_chunks.chunk_text
             IS DISTINCT FROM EXCLUDED.chunk_text
        THEN NULL
        ELSE clinical_chunks.embedding
        END,
        chunk_text = EXCLUDED.chunk_text
    """

    # These are the clinical source tables currently included
    # by get_all_clinical_text_sources_for_chunking().
    source_tables = [
        "clinical_content",
        "consultation_history",
        "consultation_diagnosis",
        "consultation_investigations",
        "consultation_medications",
        "consultation_procedures",
    ]

    try:
        # Validate the chunks before changing the database.
        consultation_ids = set()

        for chunk in chunks:
            if not chunk.get("source_table"):
                raise ValueError("source_table cannot be empty")

            if chunk["source_table"] not in source_tables:
                raise ValueError(
                    f"Unsupported clinical source table: " f"{chunk['source_table']}"
                )

            if not chunk.get("source_record_id"):
                raise ValueError("source_record_id cannot be empty")

            if not chunk.get("chunk_text", "").strip():
                raise ValueError("chunk_text cannot be empty")

            consultation_ids.add(chunk["consultation_id"])

        connection = get_postgres_connection()

        with connection.cursor() as cursor:
            # Remove old chunks for the consultations being rebuilt.
            # Keep unrelated consultation data and other source tables.
            for consultation_id in consultation_ids:
                cursor.execute(
                    """
                    DELETE FROM clinical_chunks
                    WHERE consultation_id = %s
                      AND source_table = ANY(%s);
                    """,
                    (consultation_id, source_tables),
                )

            # Insert the freshly generated chunks.
            for chunk in chunks:
                cursor.execute(
                    insert_query,
                    (
                        chunk["consultation_id"],
                        chunk["source_table"],
                        chunk["source_record_id"],
                        chunk["section_name"],
                        chunk["chunk_text"],
                        chunk["chunk_index"],
                    ),
                )

        # Delete and insert operations succeed or fail together.
        connection.commit()

        logger.info(
            "Clinical chunks rebuilt | consultations=%s | chunks_saved=%s",
            len(consultation_ids),
            len(chunks),
        )

        return len(chunks)

    except Exception as error:
        if connection is not None:
            connection.rollback()

        logger.exception("Failed to rebuild clinical chunks")
        raise RuntimeError("Unable to rebuild clinical chunks") from error

    finally:
        if connection is not None:
            connection.close()


def get_chunks_missing_embeddings(
    consultation_id: int | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Retrieve clinical chunks that do not yet have embeddings."""
    if limit < 1:
        raise ValueError("Limit must be greater than zero.")

    query = """
        SELECT
            chunk_id,
            consultation_id,
            source_table,
            source_record_id,
            section_name,
            chunk_text
        FROM clinical_chunks
        WHERE embedding IS NULL
    """
    params: list[Any] = []

    if consultation_id is not None:
        query += " AND consultation_id = %s"
        params.append(consultation_id)

    query += " ORDER BY consultation_id, chunk_index LIMIT %s"
    params.append(limit)

    with get_postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


def save_chunk_embedding(
    chunk_id: Any,
    embedding: list[float],
) -> None:
    """Save an embedding vector against an existing clinical chunk."""
    if len(embedding) != 1536:
        raise ValueError("Embedding must contain exactly 1536 dimensions.")

    with get_postgres_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE clinical_chunks
                SET embedding = %s
                WHERE chunk_id = %s
                """,
                (embedding, chunk_id),
            )

            if cursor.rowcount != 1:
                raise ValueError("Expected to update exactly one clinical chunk.")


def search_similar_clinical_chunks(
    query_embedding: list[float],
    limit: int = 5,
    consultation_id: int | None = None,
    source_table: str | None = None,
) -> list[dict[str, Any]]:
    """

        Retrieve the most semantically similar clinical chunks.

        Args:
            query_embedding: Embedding vector generated from the user's query.
            limit: Maximum number of chunks to return.
            consultation_id: Optional consultation filter.

        Returns:
            Ranked clinical chunks with source metadata and cosine distance.
            What this function does
    - Uses <=>, pgvector's cosine distance operator.
    - Returns the closest matching chunks first; a smaller distance means a closer match.
    - Optionally restricts results to one consultation.
    - Returns source metadata so future RAG responses can reference the clinical records they used.
    - Does not modify your existing ingestion or embedding logic.
    """
    if len(query_embedding) != 1536:
        raise ValueError("Query embedding must contain 1536 dimensions.")

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100.")

    # Only allow source tables supported by the clinical retrieval pipeline.
    allowed_source_tables = {
        "clinical_content",
        "consultation_history",
        "consultation_diagnosis",
        "consultation_investigations",
        "consultation_medications",
        "consultation_procedures",
    }

    if source_table is not None and source_table not in allowed_source_tables:
        raise ValueError("Unsupported clinical source table.")

    connection = None

    try:
        connection = get_postgres_connection()
        register_vector(connection)

        with connection.cursor() as cursor:
            sql = """
                SELECT
                    chunk_id,
                    consultation_id,
                    source_table,
                    source_record_id,
                    section_name,
                    chunk_text,
                    chunk_index,
                    embedding <=> %s AS cosine_distance
                FROM clinical_chunks
                WHERE embedding IS NOT NULL
            """

            # Explicitly adapt the query embedding as a PostgreSQL vector.
            query_vector = Vector(query_embedding)

            params: list[Any] = [query_vector]

            if consultation_id is not None:
                sql += " AND consultation_id = %s"
                params.append(consultation_id)
            # Restrict results to a specific source table when requested.
            if source_table is not None:
                sql += " AND source_table = %s"
                params.append(source_table)

            sql += """
                ORDER BY embedding <=> %s
                LIMIT %s
            """

            # Use the same vector object for the ORDER BY comparison.
            params.extend([query_vector, limit])

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            columns = [column.name for column in cursor.description]

            return [dict(zip(columns, row)) for row in rows]

    except Exception:
        logger.exception("Clinical vector search failed.")
        raise

    finally:
        if connection is not None:
            connection.close()


def search_keyword_clinical_chunks(
    query: str,
    limit: int = 5,
    consultation_id: int | None = None,
    source_table: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search clinical chunks using PostgreSQL full-text search.

    Returns matching chunks ranked by keyword relevance.
    Optional consultation and source filters restrict the results.
    """
    if not query or not query.strip():
        raise ValueError("Search query must not be empty.")

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100.")

    allowed_source_tables = {
        "clinical_content",
        "consultation_history",
        "consultation_diagnosis",
        "consultation_investigations",
        "consultation_medications",
        "consultation_procedures",
    }

    if source_table is not None and source_table not in allowed_source_tables:
        raise ValueError("Unsupported clinical source table.")

    connection = None

    try:
        connection = get_postgres_connection()

        with connection.cursor() as cursor:

            sql = """
    SELECT
        chunk_id,
        consultation_id,
        source_table,
        source_record_id,
        section_name,
        chunk_text,
        chunk_index,
        ts_rank(
            search_vector,
            (
                SELECT string_agg(term, ' | ')::tsquery
                FROM unnest(
                    string_to_array(
                        websearch_to_tsquery('english', %s)::text,
                        ' & '
                    )
                ) AS term
            )
        ) AS keyword_rank
    FROM clinical_chunks
    WHERE search_vector @@
        (
            SELECT string_agg(term, ' | ')::tsquery
            FROM unnest(
                string_to_array(
                    websearch_to_tsquery('english', %s)::text,
                    ' & '
                )
            ) AS term
        )
"""

            params: list[Any] = [query, query]

            if consultation_id is not None:
                sql += " AND consultation_id = %s"
                params.append(consultation_id)

            if source_table is not None:
                sql += " AND source_table = %s"
                params.append(source_table)

            sql += """
                ORDER BY keyword_rank DESC
                LIMIT %s
            """
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            columns = [column.name for column in cursor.description]

            return [dict(zip(columns, row)) for row in rows]

    except Exception:
        logger.exception("Clinical keyword search failed.")
        raise

    finally:
        if connection is not None:
            connection.close()
