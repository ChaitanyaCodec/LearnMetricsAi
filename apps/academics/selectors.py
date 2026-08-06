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

from django.db.models import QuerySet

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

def get_institutions() -> QuerySet[Institution]:
    """
    Return all institutions.
    """

    return Institution.objects.order_by("name")

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

def get_departments() -> QuerySet[Department]:
    """
    Return all departments.
    """

    return (
        Department.objects
        .select_related("institution")
        .order_by("name")
    )

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


def get_courses() -> QuerySet[Course]:
    """
    Return all courses.
    """

    return (
        Course.objects
        .select_related("department")
        .order_by("name")
    )

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

def get_semesters() -> QuerySet[Semester]:
    """
    Return all semesters.
    """

    return (
        Semester.objects
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

def get_subjects() -> QuerySet[Subject]:
    """
    Return all subjects.
    """

    return (
        Subject.objects
        .select_related(
            "semester",
            "semester__course",
            "semester__course__department",
            "semester__course__department__institution",
        )
        .order_by("name")
    )


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