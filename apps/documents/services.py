import hashlib
import logging
from pathlib import Path

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.rag.indexing import index_document_version

from .models import Document, DocumentVersion
from .permissions import (
    can_manage_document,
    is_documents_admin,
    teacher_can_upload_for_subject,
)
from .validators import validate_document_file


logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    pass


def calculate_file_checksum(uploaded_file):
    checksum = hashlib.sha256()

    for chunk in uploaded_file.chunks():
        checksum.update(chunk)

    uploaded_file.seek(0)

    return checksum.hexdigest()


def _get_file_metadata(uploaded_file):
    return {
        "original_filename": Path(uploaded_file.name).name,
        "content_type": getattr(uploaded_file, "content_type", "") or "",
        "file_size": uploaded_file.size,
        "file_checksum": calculate_file_checksum(uploaded_file),
    }


def _assert_can_create_document(user, subject):
    if is_documents_admin(user):
        return

    if teacher_can_upload_for_subject(user, subject):
        return

    raise DocumentServiceError(
        "You are not authorized to upload documents for this subject."
    )


def _assert_can_upload_new_version(user, document):
    if is_documents_admin(user):
        return

    if not can_manage_document(user, document):
        raise DocumentServiceError(
            "You are not authorized to upload a new version of this document."
        )

    if not teacher_can_upload_for_subject(user, document.subject):
        raise DocumentServiceError(
            "You no longer have an active teaching assignment for this subject."
        )


@transaction.atomic
def create_document_with_initial_version(
    *,
    user,
    title,
    description,
    subject,
    source_file,
):
    """
    Create a logical document and its first uploaded version.
    """
    _assert_can_create_document(user, subject)
    validate_document_file(source_file)

    document = Document.objects.create(
        title=title.strip(),
        description=description.strip(),
        subject=subject,
        created_by=user,
    )

    return DocumentVersion.objects.create(
        document=document,
        version_number=1,
        source_file=source_file,
        uploaded_by=user,
        **_get_file_metadata(source_file),
    )


@transaction.atomic
def upload_new_document_version(
    *,
    user,
    document_id,
    source_file,
):
    """
    Add the next sequential version to an existing document.

    Document review/lifecycle status is intentionally not changed here;
    that is handled in 7C-I13.
    """
    document = (
        Document.objects
        .select_for_update()
        .select_related("subject", "subject__semester")
        .filter(pk=document_id)
        .first()
    )

    if document is None:
        raise DocumentServiceError("Document not found.")

    _assert_can_upload_new_version(user, document)
    validate_document_file(source_file)

    latest_version = document.versions.aggregate(
        latest=Max("version_number")
    )["latest"] or 0

    return DocumentVersion.objects.create(
        document=document,
        version_number=latest_version + 1,
        source_file=source_file,
        uploaded_by=user,
        **_get_file_metadata(source_file),
    )


@transaction.atomic
def submit_latest_version_for_review(*, user, document_id):
    document = (
        Document.objects
        .select_for_update()
        .select_related("subject", "subject__semester")
        .get(pk=document_id)
    )

    if document.status == Document.Status.RETIRED:
        raise DocumentServiceError(
            "A retired document cannot be submitted for review."
        )

    _assert_can_upload_new_version(user, document)

    version = (
        document.versions
        .select_for_update()
        .order_by("-version_number")
        .first()
    )

    if version is None:
        raise DocumentServiceError(
            "This document has no uploaded version."
        )

    if (
        version.processing_status
        != DocumentVersion.ProcessingStatus.COMPLETED
    ):
        raise DocumentServiceError(
            "The latest version must finish processing before review."
        )

    if version.review_status not in [
        DocumentVersion.ReviewStatus.DRAFT,
        DocumentVersion.ReviewStatus.REJECTED,
    ]:
        raise DocumentServiceError(
            "Only draft or rejected versions can be submitted for review."
        )

    version.review_status = (
        DocumentVersion.ReviewStatus.PENDING_REVIEW
    )
    version.reviewed_by = None
    version.reviewed_at = None
    version.rejection_reason = ""
    version.save(
        update_fields=[
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ]
    )

    document.status = Document.Status.PENDING_REVIEW
    document.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return version


@transaction.atomic
def approve_document_version(*, user, document_version_id):
    if not is_documents_admin(user):
        raise DocumentServiceError(
            "Only administrators can approve document versions."
        )

    version = (
        DocumentVersion.objects
        .select_for_update()
        .get(pk=document_version_id)
    )

    document = (
        Document.objects
        .select_for_update()
        .get(pk=version.document_id)
    )

    if (
        version.review_status
        != DocumentVersion.ReviewStatus.PENDING_REVIEW
    ):
        raise DocumentServiceError(
            "Only versions pending review can be approved."
        )

    if (
        version.processing_status
        != DocumentVersion.ProcessingStatus.COMPLETED
    ):
        raise DocumentServiceError(
            "Only successfully processed versions can be approved."
        )

    version.review_status = (
        DocumentVersion.ReviewStatus.APPROVED
    )
    version.reviewed_by = user
    version.reviewed_at = timezone.now()
    version.rejection_reason = ""
    version.save(
        update_fields=[
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ]
    )

    document.published_version = version
    document.status = Document.Status.APPROVED
    document.is_active = True
    document.save(
        update_fields=[
            "published_version",
            "status",
            "is_active",
            "updated_at",
        ]
    )

    def index_approved_version():
        try:
            index_document_version(
                document_version_id=version.id,
            )
        except Exception:
            logger.exception(
                "RAG indexing failed for approved "
                "document version %s.",
                version.id,
            )

    transaction.on_commit(index_approved_version)

    return version


@transaction.atomic
def reject_document_version(
    *,
    user,
    document_version_id,
    reason,
):
    if not is_documents_admin(user):
        raise DocumentServiceError(
            "Only administrators can reject document versions."
        )

    reason = reason.strip()

    if not reason:
        raise DocumentServiceError(
            "A rejection reason is required."
        )

    version = (
        DocumentVersion.objects
        .select_for_update()
        .get(pk=document_version_id)
    )

    document = (
        Document.objects
        .select_for_update()
        .get(pk=version.document_id)
    )

    if (
        version.review_status
        != DocumentVersion.ReviewStatus.PENDING_REVIEW
    ):
        raise DocumentServiceError(
            "Only versions pending review can be rejected."
        )

    version.review_status = (
        DocumentVersion.ReviewStatus.REJECTED
    )
    version.reviewed_by = user
    version.reviewed_at = timezone.now()
    version.rejection_reason = reason
    version.save(
        update_fields=[
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ]
    )

    document.status = (
        Document.Status.APPROVED
        if document.published_version_id
        else Document.Status.REJECTED
    )
    document.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return version


@transaction.atomic
def retire_document(*, user, document_id, reason):
    if not is_documents_admin(user):
        raise DocumentServiceError(
            "Only administrators can retire documents."
        )

    reason = reason.strip()

    if not reason:
        raise DocumentServiceError(
            "A retirement reason is required."
        )

    document = (
        Document.objects
        .select_for_update()
        .get(pk=document_id)
    )

    document.status = Document.Status.RETIRED
    document.is_active = False
    document.retired_by = user
    document.retired_at = timezone.now()
    document.retirement_reason = reason
    document.save(
        update_fields=[
            "status",
            "is_active",
            "retired_by",
            "retired_at",
            "retirement_reason",
            "updated_at",
        ]
    )

    return document