
"""
RAG domain models.

Embedding and vector-storage models are intentionally deferred
to the embedding and pgvector phases.
Contains vector embeddings, conversations, and chat messages
used by the LearnMetrics AI assistant.
"""
import uuid
from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from apps.academics.models import Subject
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

class Conversation(models.Model):
    """
    Persistent AI assistant conversation belonging to one user
    and one academic subject.
    """


    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rag_conversations",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="rag_conversations",
    )

    title = models.CharField(
        max_length=255,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        if self.title:
            return self.title

        return (
            f"Conversation {self.id} "
            f"for {self.subject}"
        )


class ChatMessage(models.Model):
    """
    One message within a persistent RAG conversation.

    Assistant messages may store deterministic source metadata
    in the JSON metadata field.
    """

    class Role(models.TextChoices):
        USER = "USER", "User"
        ASSISTANT = "ASSISTANT", "Assistant"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
    )

    content = models.TextField()

    sequence = models.PositiveIntegerField()

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["sequence", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "sequence"],
                name="unique_message_sequence_per_conversation",
            ),
        ]

    def __str__(self):
        return (
            f"{self.role} message "
            f"{self.sequence} "
            f"in conversation {self.conversation_id}"
        )