from django.conf import settings


# ---------------------------------------------------------------------------
# Chunk indexing configuration
# ---------------------------------------------------------------------------

INDEXING_BATCH_SIZE = getattr(
    settings,
    "RAG_INDEXING_BATCH_SIZE",
    32,
)


INDEXING_MAX_CHUNK_LENGTH = getattr(
    settings,
    "RAG_INDEXING_MAX_CHUNK_LENGTH",
    10000,
)