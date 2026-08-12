"""
Read/query logic for the Teachers module.

Selectors contain database read operations only.
They do not create, update, or delete records.
"""

from __future__ import annotations

from typing import Optional

from django.db.models import Q, QuerySet

from .models import Teacher, TeachingAssignment


def get_teachers(
    *,
    search: Optional[str] = None,
    filters: Optional[dict] = None,
    ordering: Optional[str] = None,
) -> QuerySet[Teacher]:
    """
    Return teachers with optional search, filters,
    and ordering.

    Compatible with the centralized BaseListView
    selector contract.
    """

    queryset = (
        Teacher.objects
        .select_related("user")
    )

    if search:
        queryset = queryset.filter(
            Q(
                employee_id__icontains=search
            )
            | Q(
                user__first_name__icontains=search
            )
            | Q(
                user__last_name__icontains=search
            )
            | Q(
                user__email__icontains=search
            )
            | Q(
                user__phone_number__icontains=search
            )
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


def get_teacher(
    teacher_id,
) -> Optional[Teacher]:
    """
    Return a single Teacher by primary key.
    """

    return (
        Teacher.objects
        .select_related("user")
        .filter(pk=teacher_id)
        .first()
    )


def get_teacher_by_user(
    user_id,
) -> Optional[Teacher]:
    """
    Return the Teacher profile belonging to a User.
    """

    return (
        Teacher.objects
        .select_related("user")
        .filter(user_id=user_id)
        .first()
    )


def get_teaching_assignments(
    *,
    search: Optional[str] = None,
    filters: Optional[dict] = None,
    ordering: Optional[str] = None,
) -> QuerySet[TeachingAssignment]:
    """
    Return teaching assignments with related academic
    and teacher information.

    Compatible with the centralized BaseListView
    selector contract.
    """

    queryset = (
        TeachingAssignment.objects
        .select_related(
            "teacher",
            "teacher__user",
            "course",
            "semester",
            "subject",
        )
    )

    if search:
        queryset = queryset.filter(
            Q(
                teacher__employee_id__icontains=search
            )
            | Q(
                teacher__user__first_name__icontains=search
            )
            | Q(
                teacher__user__last_name__icontains=search
            )
            | Q(
                teacher__user__email__icontains=search
            )
            | Q(
                course__name__icontains=search
            )
            | Q(
                course__code__icontains=search
            )
            | Q(
                semester__name__icontains=search
            )
            | Q(
                subject__name__icontains=search
            )
            | Q(
                subject__code__icontains=search
            )
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


def get_teacher_assignments(
    teacher_id,
    *,
    search: Optional[str] = None,
    filters: Optional[dict] = None,
    ordering: Optional[str] = None,
) -> QuerySet[TeachingAssignment]:
    """
    Return assignments belonging to one Teacher.

    This will later be used by the Teacher-facing
    dashboard to restrict academic data to the
    teacher's actual assignments.
    """

    queryset = get_teaching_assignments(
        search=search,
        filters=filters,
        ordering=ordering,
    )

    return queryset.filter(
        teacher_id=teacher_id
    )