from django.db import transaction
from django.utils import timezone

from .chunkers import chunk_text
from .extractors import (
    DocumentExtractionError,
    extract_document_version,
)
from .models import DocumentChunk, DocumentVersion


class DocumentProcessingError(Exception):
    pass


def _start_processing(document_version_id):
    with transaction.atomic():
        document_version = (
            DocumentVersion.objects
            .select_for_update()
            .get(pk=document_version_id)
        )

        if (
            document_version.processing_status
            == DocumentVersion.ProcessingStatus.PROCESSING
        ):
            raise DocumentProcessingError(
                "This document version is already processing."
            )

        document_version.processing_status = (
            DocumentVersion.ProcessingStatus.PROCESSING
        )
        document_version.processing_started_at = timezone.now()
        document_version.processing_completed_at = None
        document_version.processing_error = ""
        document_version.save(
            update_fields=[
                "processing_status",
                "processing_started_at",
                "processing_completed_at",
                "processing_error",
                "updated_at",
            ]
        )

        return document_version


def _mark_processing_failed(
    document_version_id,
    error_message,
):
    DocumentVersion.objects.filter(
        pk=document_version_id
    ).update(
        processing_status=DocumentVersion.ProcessingStatus.FAILED,
        processing_completed_at=timezone.now(),
        processing_error=error_message,
    )


def process_document_version(document_version_id):
    """
    Extract, chunk, and persist one document version.

    This currently runs in-process. It is deliberately designed so
    a future background worker can call this same function.
    """
    document_version = _start_processing(document_version_id)

    try:
        extraction_result = extract_document_version(
            document_version
        )

        chunks = chunk_text(extraction_result.text)

        with transaction.atomic():
            locked_version = (
                DocumentVersion.objects
                .select_for_update()
                .get(pk=document_version_id)
            )

            DocumentChunk.objects.filter(
                document_version=locked_version
            ).delete()

            DocumentChunk.objects.bulk_create(
                [
                    DocumentChunk(
                        document_version=locked_version,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        character_start=chunk.character_start,
                        character_end=chunk.character_end,
                        metadata={},
                    )
                    for chunk in chunks
                ]
            )

            locked_version.extracted_text = (
                extraction_result.text
            )
            locked_version.page_count = (
                extraction_result.page_count
            )
            locked_version.chunk_count = len(chunks)
            locked_version.processing_status = (
                DocumentVersion.ProcessingStatus.COMPLETED
            )
            locked_version.processing_completed_at = timezone.now()
            locked_version.processing_error = ""
            locked_version.save(
                update_fields=[
                    "extracted_text",
                    "page_count",
                    "chunk_count",
                    "processing_status",
                    "processing_completed_at",
                    "processing_error",
                    "updated_at",
                ]
            )

        return locked_version

    except DocumentExtractionError as exc:
        _mark_processing_failed(
            document_version_id,
            str(exc),
        )
        raise

    except Exception as exc:
        _mark_processing_failed(
            document_version_id,
            f"Unexpected processing error: {exc}",
        )
        raise