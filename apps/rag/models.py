
"""
RAG domain models.

Embedding and vector-storage models are intentionally deferred
to the embedding and pgvector phases.
"""


from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from apps.documents.models import DocumentChunk


class ChunkEmbedding(models.Model):
    """
    Vector embedding generated for a document chunk.

    RAG owns embedding data separately from the Documents app so that
    embedding models can be changed or re-indexed independently.
    """

    document_chunk = models.OneToOneField(
        DocumentChunk,
        on_delete=models.CASCADE,
        related_name="embedding_record",
    )

    embedding = VectorField(
        dimensions=settings.RAG_EMBEDDING_DIMENSIONS,
    )

    model_name = models.CharField(
        max_length=255,
    )

    model_version = models.CharField(
        max_length=100,
        blank=True,
    )

    dimensions = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["document_chunk"]

    def __str__(self):
        return (
            f"Embedding for chunk "
            f"{self.document_chunk_id}"
        )