"""
Dashboard selectors.

Read-only ORM queries for dashboard services. Existing administrator
selectors are retained; teacher/student selectors are scoped to the
current user's academic access.
"""
from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone

from apps.academics.models import Subject
from apps.documents.models import Document, DocumentVersion
from apps.students.models import StudentEnrollment
from apps.teachers.models import TeachingAssignment

User = get_user_model()


def get_total_students() -> int:
    return User.objects.filter(role=User.Roles.STUDENT).count()


def get_total_teachers() -> int:
    return User.objects.filter(role=User.Roles.TEACHER).count()


def get_total_admins() -> int:
    return User.objects.filter(role=User.Roles.ADMIN).count()


def get_active_users_count() -> int:
    return User.objects.filter(is_active=True).count()


def get_recent_users(limit: int = 10) -> QuerySet[Any]:
    return (
        User.objects.only(
            "id", "first_name", "last_name", "email",
            "role", "date_joined", "is_active",
        ).order_by("-date_joined")[:limit]
    )


def get_recently_active_users(limit: int = 10) -> QuerySet[Any]:
    return (
        User.objects.exclude(last_login__isnull=True)
        .only("id", "first_name", "last_name", "email", "last_login", "role")
        .order_by("-last_login")[:limit]
    )


def get_new_users_today() -> int:
    today = timezone.localdate()
    return User.objects.filter(date_joined__date=today).count()


def get_teacher_assignments(user) -> QuerySet:
    """Active subject assignments belonging to the logged-in teacher."""
    try:
        teacher = user.teacher_profile
    except Exception:
        return TeachingAssignment.objects.none()

    return (
        TeachingAssignment.objects.filter(
            teacher=teacher,
            is_active=True,
            subject__is_active=True,
            semester__is_active=True,
            course__is_active=True,
        )
        .select_related("subject", "semester", "course")
        .order_by("course__name", "semester__semester_number", "subject__name")
    )


def get_teacher_dashboard_data(user) -> dict:
    assignments = get_teacher_assignments(user)
    subject_ids = assignments.values_list("subject_id", flat=True).distinct()
    course_ids = assignments.values_list("course_id", flat=True).distinct()

    own_documents = Document.objects.filter(
        created_by=user,
        subject_id__in=subject_ids,
        is_active=True,
    )

    return {
        "assigned_subjects": assignments.values("subject_id").distinct().count(),
        "assigned_courses": course_ids.count(),
        "my_documents_count": own_documents.count(),
        "pending_review_count": own_documents.filter(
            status=Document.Status.PENDING_REVIEW
        ).count(),
        "assigned_subject_list": assignments[:8],
        "recent_documents": own_documents.select_related("subject").order_by("-created_at")[:6],
    }


def get_student_dashboard_data(user) -> dict:
    try:
        student = user.student_profile
    except Exception:
        return {
            "active_enrollments": 0,
            "enrolled_subjects": 0,
            "available_materials": 0,
            "recent_materials": Document.objects.none(),
            "enrollments": StudentEnrollment.objects.none(),
        }

    enrollments = StudentEnrollment.objects.filter(
        student=student,
        status=StudentEnrollment.Status.ACTIVE,
        is_active=True,
        course__is_active=True,
        semester__is_active=True,
    ).select_related("course", "semester").order_by(
        "course__name", "semester__semester_number"
    )

    subject_ids = Subject.objects.filter(
        semester__student_enrollments__in=enrollments,
        is_active=True,
        semester__is_active=True,
        semester__course__is_active=True,
    ).values_list("id", flat=True).distinct()

    available = Document.objects.filter(
        subject_id__in=subject_ids,
        status=Document.Status.APPROVED,
        is_active=True,
        published_version__isnull=False,
        published_version__is_active=True,
        published_version__review_status=DocumentVersion.ReviewStatus.APPROVED,
        published_version__processing_status=DocumentVersion.ProcessingStatus.COMPLETED,
    ).select_related("subject", "published_version").distinct()

    return {
        "active_enrollments": enrollments.count(),
        "enrolled_subjects": subject_ids.count(),
        "available_materials": available.count(),
        "recent_materials": available.order_by("-updated_at")[:6],
        "enrollments": enrollments[:6],
    }
