"""
Academic services.

This module contains business logic for the academics application.

Responsibilities:
- Create academic records
- Update academic records
- Enforce business rules
- Coordinate model operations

Views should call services instead of interacting with models directly.
"""

from __future__ import annotations

from .models import (
    Institution,
    Department,
    Course,
    Semester,
    Subject,
)

#-------------------------------
#     Institution Services  
#-------------------------------

def create_institution(**data) -> Institution:
    """
    Create a new institution.
    """

    return Institution.objects.create(**data)

def update_institution(
    institution: Institution,
    **data,
) -> Institution:
    """
    Update an existing institution.
    """

    for field, value in data.items():
        setattr(institution, field, value)

    institution.save()

    return institution

def delete_institution(
    institution: Institution,
) -> None:
    """
    Delete an institution.
    """

    institution.delete()

#------------------------------
#     Department Services
#------------------------------
def create_department(**data) -> Department:
    """
    Create a new department.
    """

    return Department.objects.create(**data)

def update_department(
    department: Department,
    **data,
) -> Department:
    """
    Update an existing department.
    """

    for field, value in data.items():
        setattr(department, field, value)

    department.save()

    return department


def delete_department(
    department: Department,
) -> None:
    """
    Delete a department.
    """

    department.delete()


# ==========================================================
# Course Services
# ==========================================================

def create_course(
    **data,
) -> Course:
    """
    Create a new course.
    """

    return Course.objects.create(**data)


def update_course(
    course: Course,
    **data,
) -> Course:
    """
    Update an existing course.
    """

    for field, value in data.items():
        setattr(course, field, value)

    course.save()

    return course


def delete_course(
    course: Course,
) -> None:
    """
    Delete a course.
    """

    course.delete()
# ==========================================================
# Semester Services
# ==========================================================

def create_semester(**data) -> Semester:
    """
    Create a new semester.
    """

    return Semester.objects.create(**data)


def update_semester(
    semester: Semester,
    **data,
) -> Semester:
    """
    Update an existing semester.
    """

    for field, value in data.items():
        setattr(semester, field, value)

    semester.save()

    return semester


def delete_semester(
    semester: Semester,
) -> None:
    """
    Delete a semester.
    """

    semester.delete()

# ==========================================================
# Subject Services
# ==========================================================

def create_subject(**data) -> Subject:
    """
    Create a new subject.
    """

    return Subject.objects.create(**data)


def update_subject(
    subject: Subject,
    **data,
) -> Subject:
    """
    Update an existing subject.
    """

    for field, value in data.items():
        setattr(subject, field, value)

    subject.save()

    return subject


def delete_subject(
    subject: Subject,
) -> None:
    """
    Delete a subject.
    """

    subject.delete()