from django.db.models import Q

from apps.accounts.models import User
from apps.students.models import StudentEnrollment

from .models import Document, DocumentVersion


def get_authorized_documents(
    *,
    user,
    search=None,
    filters=None,
):
    """
    Return only documents the current user is allowed to see.
    """
    queryset = (
        Document.objects
        .select_related(
            "subject",
            "subject__semester",
            "subject__semester__course",
            "subject__semester__course__department",
            "subject__semester__course__department__institution",
            "created_by",
            "published_version",
        )
    )

    if user.role == User.Roles.ADMIN:
        pass

    elif user.role == User.Roles.TEACHER:
        queryset = queryset.filter(
            Q(created_by=user)
            | Q(
                published_version__isnull=False,
                is_active=True,
                #status__ne=Document.Status.RETIRED,
                subject__teaching_assignments__teacher__user=user,
                subject__teaching_assignments__is_active=True,
            )
        ).distinct()
        queryset = queryset.exclude(
            status=Document.Status.RETIRED
        )


    elif user.role == User.Roles.STUDENT:
        queryset = queryset.filter(
            is_active=True,
            published_version__isnull=False,
            subject__semester__student_enrollments__student__user=user,
            subject__semester__student_enrollments__status=(
                StudentEnrollment.Status.ACTIVE
            ),
            subject__semester__student_enrollments__is_active=True,
        ).exclude(
            status=Document.Status.RETIRED
        ).distinct()

    else:
        return Document.objects.none()

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(subject__name__icontains=search)
            | Q(subject__code__icontains=search)
        )

    if filters:
        if filters.get("subject"):
            queryset = queryset.filter(
                subject_id=filters["subject"]
            )

        if filters.get("status") and (
            user.role == User.Roles.ADMIN
        ):
            queryset = queryset.filter(
                status=filters["status"]
            )

    return queryset.order_by("-created_at")


def get_authorized_document(*, user, document_id):
    return get_authorized_documents(
        user=user
    ).filter(
        pk=document_id
    ).first()


def get_admin_review_queue():
    return (
        DocumentVersion.objects
        .filter(
            review_status=(
                DocumentVersion.ReviewStatus.PENDING_REVIEW
            )
        )
        .select_related(
            "document",
            "document__subject",
            "uploaded_by",
        )
        .order_by("created_at")
    )