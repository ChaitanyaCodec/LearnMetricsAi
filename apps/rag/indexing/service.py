from django.conf import settings

from apps.documents.models import Document, DocumentChunk, DocumentVersion

from ..embeddings import EmbeddingService
from ..models import ChunkEmbedding
from .exceptions import IndexingError


def _get_indexable_version(document_version_id):
    """
    Return a document version only when it is the currently
    published and approved version of an active document.
    """

    version = (
        DocumentVersion.objects
        .select_related("document")
        .filter(
            pk=document_version_id,
            document__is_active=True,
            document__status=Document.Status.APPROVED,
            document__published_version_id=document_version_id,
            review_status=DocumentVersion.ReviewStatus.APPROVED,
            processing_status=DocumentVersion.ProcessingStatus.COMPLETED,
        )
        .first()
    )

    if version is None:
        raise IndexingError(
            "Document version is not eligible for RAG indexing."
        )

    return version


def index_chunk(*, chunk, embedding_service=None):
    """
    Generate and persist an embedding for one document chunk.

    Existing embeddings are updated so indexing is idempotent.
    """

    if not isinstance(chunk, DocumentChunk):
        raise IndexingError(
            "A valid DocumentChunk instance is required."
        )

    content = chunk.content.strip()

    if not content:
        raise IndexingError(
            f"Document chunk {chunk.pk} has no content."
        )

    if embedding_service is None:
        embedding_service = EmbeddingService()

    try:
        vector = embedding_service.embed_text(content)
    except Exception as exc:
        raise IndexingError(
            f"Failed to generate embedding for chunk {chunk.pk}."
        ) from exc

    dimensions = len(vector)

    if dimensions != settings.RAG_EMBEDDING_DIMENSIONS:
        raise IndexingError(
            "Generated embedding dimension does not match "
            "the configured RAG embedding dimension."
        )

    embedding_record, _ = ChunkEmbedding.objects.update_or_create(
        document_chunk=chunk,
        defaults={
            "embedding": vector,
            "model_name": settings.RAG_EMBEDDING_MODEL,
            "model_version": getattr(
                settings,
                "RAG_EMBEDDING_MODEL_VERSION",
                "",
            ),
            "dimensions": dimensions,
        },
    )

    return embedding_record


def index_document_version(*, document_version_id):
    """
    Index all chunks belonging to the currently published,
    approved document version.

    Returns the number of successfully indexed chunks.
    """

    version = _get_indexable_version(document_version_id)

    chunks = (
        DocumentChunk.objects
        .filter(document_version=version)
        .order_by("chunk_index")
    )

    embedding_service = EmbeddingService()

    indexed_count = 0

    for chunk in chunks:
        index_chunk(
            chunk=chunk,
            embedding_service=embedding_service,
        )
        indexed_count += 1

    return indexed_count