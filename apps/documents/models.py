from django.conf import settings
from django.db import models

from apps.academics.models import Subject
from apps.core.models import BaseModel
from .validators import validate_document_file
from .storage import private_document_storage

class Document(BaseModel):
    """
    Logical learning document scoped to one academic subject.

    File uploads belong to DocumentVersion, not this model.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        RETIRED = "RETIRED", "Retired"

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="documents",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_documents",
    )
    published_version = models.ForeignKey(
        "DocumentVersion",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )

    retired_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="retired_documents",
        null=True,
        blank=True,
    )

    retired_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    retirement_reason = models.TextField(
        blank=True,
    )

    class Meta:
                ordering = ["-created_at"]
                verbose_name = "Document"
                verbose_name_plural = "Documents"

    def __str__(self):
        return self.title


def document_version_upload_path(instance, filename):
    return (
        f"documents/{instance.document_id}/"
        f"versions/{instance.version_number}/{filename}"
    )


class DocumentVersion(BaseModel):
    """
    A stored source-file version of a logical Document.
    """

    class ProcessingStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    class ReviewStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    document = models.ForeignKey(
            Document,
            on_delete=models.CASCADE,
            related_name="versions",
        )

    version_number = models.PositiveIntegerField()

    source_file = models.FileField(
        upload_to=document_version_upload_path,
        storage=private_document_storage,
        validators=[validate_document_file],
    )

    original_filename = models.CharField(
        max_length=255,
    )

    content_type = models.CharField(
        max_length=100,
        blank=True,
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
    )

    file_checksum = models.CharField(
        max_length=64,
        blank=True,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_document_versions",
    )
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.DRAFT,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_document_versions",
        null=True,
        blank=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )

    processing_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    processing_completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    processing_error = models.TextField(
        blank=True,
    )

    extracted_text = models.TextField(
        blank=True,
    )

    page_count = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    chunk_count = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["document", "-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_number"],
                name="unique_document_version_number",
            ),
        ]
        verbose_name = "Document version"
        verbose_name_plural = "Document versions"

    def __str__(self):
        return f"{self.document.title} (v{self.version_number})"

class DocumentChunk(BaseModel):
    """
    A searchable text segment extracted from one document version.

    Embeddings are intentionally deferred until the RAG phase.
    """

    document_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    chunk_index = models.PositiveIntegerField()

    content = models.TextField()

    page_number = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    character_start = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    character_end = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = ["document_version", "chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["document_version", "chunk_index"],
                name="unique_chunk_index_per_document_version",
            ),
        ]
        verbose_name = "Document chunk"
        verbose_name_plural = "Document chunks"

    def __str__(self):
        return (
            f"{self.document_version} "
            f"- chunk {self.chunk_index}"
        )