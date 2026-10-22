"""Compare a regenerated embedding with one stored in PostgreSQL."""

from pgvector.psycopg import register_vector
from pgvector import Vector
from clinical_ai_pipeline.services.embedding_service import (
    EmbeddingService,
)
from clinical_ai_pipeline.storage.postgres_client import (
    get_postgres_connection,
)

# Paste the de-identified chunk text copied from PostgreSQL.
chunk_text = """NEBZMART G SMARTULES | Dose: 1-0-1 | Daily | Frequency: | Duration: | D | Quantity:"""

embedding_service = EmbeddingService()

# Generate a new embedding using the same service as ingestion.
new_embedding = embedding_service.generate_embedding(chunk_text)

connection = get_postgres_connection()

try:
    register_vector(connection)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT embedding
            FROM clinical_chunks
            WHERE chunk_text = %s
              AND embedding IS NOT NULL
            LIMIT 1
            """,
            (chunk_text,),
        )

        row = cursor.fetchone()

        if row is None:
            raise ValueError("No stored embedding found for this chunk.")

        stored_embedding = row[0].to_list()
finally:
    connection.close()

# Compare the regenerated vector with the stored vector.
differences = [
    abs(new - stored) for new, stored in zip(new_embedding, stored_embedding)
]

print("New embedding dimensions:", len(new_embedding))
print("Stored embedding dimensions:", len(stored_embedding))
print("Exactly equal:", new_embedding == stored_embedding)
print("Maximum absolute difference:", max(differences))
print(
    "Mean absolute difference:",
    sum(differences) / len(differences),
)
print("Embedding comparison completed.")
