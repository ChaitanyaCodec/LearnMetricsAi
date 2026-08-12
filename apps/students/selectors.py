"""
Student selectors.

Selectors contain read-only database queries.

Rules:
- Read operations only.
- No create/update/delete operations.
- No business logic.
"""

from __future__ import annotations

from django.db.models import Q, QuerySet

from .models import Student, StudentEnrollment


def get_students(
    *,
    search=None,
    filters=None,
    ordering=None,
) -> QuerySet[Student]:
    """
    Return students with optional search, filters,
    and ordering.
    """

    queryset = Student.objects.select_related(
        "user",
    )

    if search:
        queryset = queryset.filter(
            Q(student_id__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
        )

    if filters:
        queryset = queryset.filter(
            **filters
        )

    if ordering:
        queryset = queryset.order_by(
            ordering
        )

    return queryset


def get_student(
    student_id,
) -> Student | None:
    """
    Return a single student by primary key.
    """

    return (
        Student.objects
        .select_related("user")
        .filter(pk=student_id)
        .first()
    )


def get_student_by_user(
    user,
) -> Student | None:
    """
    Return the Student profile associated
    with a User.
    """

    return (
        Student.objects
        .select_related("user")
        .filter(user=user)
        .first()
    )


def get_student_enrollments(
    *,
    search=None,
    student=None,
    filters=None,
    ordering=None,
) -> QuerySet[StudentEnrollment]:
    """
    Return student enrollments with related academic information.

    Compatible with the centralized BaseListView selector contract.
    """

    queryset = (
        StudentEnrollment.objects
        .select_related(
            "student",
            "student__user",
            "course",
            "semester",
        )
    )

    if search:
        queryset = queryset.filter(
            Q(
                student__student_id__icontains=search
            )
            | Q(
                student__user__first_name__icontains=search
            )
            | Q(
                student__user__last_name__icontains=search
            )
            | Q(
                student__user__email__icontains=search
            )
            | Q(
                roll_number__icontains=search
            )
            | Q(
                academic_year__icontains=search
            )
        )

    if student is not None:
        queryset = queryset.filter(
            student=student
        )

    if filters:
        queryset = queryset.filter(
            **filters
        )

    if ordering:
        queryset = queryset.order_by(
            ordering
        )

    return queryset


def get_active_enrollments() -> QuerySet[StudentEnrollment]:
    """
    Return active student enrollments.
    """

    return (
        StudentEnrollment.objects
        .filter(
            status=StudentEnrollment.Status.ACTIVE
        )
        .select_related(
            "student",
            "student__user",
            "course",
            "semester",
        )
        .order_by(
            "course",
            "semester",
            "roll_number",
        )
    )