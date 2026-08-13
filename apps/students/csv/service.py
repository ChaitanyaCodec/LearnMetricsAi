"""
CSV import service for the Students module.

This module handles the common import workflow for
Student CSV imports.

Student-specific validation and object creation
remain inside student.py.
"""

from django.db import transaction,IntegrityError


class StudentCSVImportError(Exception):
    """
    Base exception for Student CSV import errors.
    """

    pass


def import_student_rows(
    rows,
    create_callback,
):
    """
    Import validated student rows atomically.

    Any database integrity failure rolls back
    the entire import.
    """

    imported_students = []

    try:

        with transaction.atomic():

            for row in rows:

                result = create_callback(row)

                imported_students.append(result)

    except IntegrityError as exc:

        raise StudentCSVImportError(
            "Student import failed because one or more "
            "records violate a database constraint. "
            "No students were imported."
        ) from exc

    return imported_students