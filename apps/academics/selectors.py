"""
Academic selectors.

This module contains read-only database queries for the
academics application.

Rules:
- Read operations only.
- No business logic.
- No create/update/delete operations.
"""

from __future__ import annotations

from django.db.models import QuerySet,Q
from apps.core.utils.query import apply_filters

from .models import (
    Institution,
    Department,
    Course,
    Semester,
    Subject,
)

#--------------------------------
#     Institution Selectors
#--------------------------------



def get_institutions(
    *,
    search=None,
    filters=None,
):
    queryset = Institution.objects.all()

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(short_name__icontains=search)
            | Q(email__icontains=search)
        )

    queryset = apply_filters(
        queryset,
        filters,
        {
            "is_active": "is_active",
        },
    )

    return queryset

def get_active_institutions() -> QuerySet[Institution]:
    """
    Return active institutions.
    """

    return Institution.objects.filter(
        is_active=True
    ).order_by("name")

#--------------------------------
#     Department Selectors
#--------------------------------
def get_departments(
    *,
    search=None,
    filters=None,
):
    """
    Return departments with optional search and filters.
    """

    queryset = Department.objects.select_related(
        "institution"
    )

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(code__icontains=search)
            | Q(institution__name__icontains=search)
        )

    queryset = apply_filters(
        queryset,
        filters,
        {
            "institution": "institution_id",
            "is_active": "is_active",
        },
    )

    return queryset

def get_active_departments() -> QuerySet[Department]:
    """
    Return active departments.
    """

    return (
        Department.objects
        .filter(is_active=True)
        .select_related("institution")
        .order_by("name")
    )

#-------------------------------
#     Course Selectors
#-------------------------------

def get_courses(
    *,
    search=None,
    filters=None,
):
    """
    Return courses with optional search and filters.
    """

    queryset = Course.objects.select_related(
        "department",
        "department__institution",
    )

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(code__icontains=search)
            | Q(department__name__icontains=search)
            | Q(
                department__institution__name__icontains=search
            )
        )

    queryset = apply_filters(
        queryset,
        filters,
        {
            "department": "department_id",
            "is_active": "is_active",
        },
    )

    return queryset

def get_active_courses() -> QuerySet[Course]:
    """
    Return active courses.
    """

    return (
        Course.objects
        .filter(is_active=True)
        .select_related("department")
        .order_by("name")
    )

# ==========================================================
# Semester Selectors
# ==========================================================


def get_semesters(
    *,
    search=None,
    filters=None,
):
    """
    Return semesters with optional search and filters.
    """

    queryset = Semester.objects.select_related(
        "course",
        "course__department",
        "course__department__institution",
    )

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(semester_number__icontains=search)
            | Q(course__name__icontains=search)
        )

    queryset = apply_filters(
        queryset,
        filters,
        {
            "course": "course_id",
            "is_active": "is_active",
        },
    )

    return queryset
def get_active_semesters() -> QuerySet[Semester]:
    """
    Return active semesters.
    """

    return (
        Semester.objects
        .filter(is_active=True)
        .select_related(
            "course",
            "course__department",
            "course__department__institution",
        )
        .order_by(
            "course",
            "semester_number",
        )
    )

# ==========================================================
# Subject Selectors
# ==========================================================



def get_subjects(
    *,
    search=None,
    filters=None,
):
    """
    Return subjects with optional search and filters.
    """

    queryset = Subject.objects.select_related(
        "semester",
        "semester__course",
        "semester__course__department",
        "semester__course__department__institution",
    )

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(code__icontains=search)
            | Q(semester__course__name__icontains=search)
            | Q(semester__name__icontains=search)
        )

    queryset = apply_filters(
        queryset,
        filters,
        {
            "semester": "semester_id",
            "is_active": "is_active",
        },
    )

    return queryset
def get_active_subjects() -> QuerySet[Subject]:
    """
    Return active subjects.
    """

    return (
        Subject.objects
        .filter(is_active=True)
        .select_related(
            "semester",
            "semester__course",
            "semester__course__department",
            "semester__course__department__institution",
        )
        .order_by("name")
    )