"""
Semester CSV import functionality.
"""

from __future__ import annotations

import csv
import io

from .service import read_csv_file

from ..models import (
    Course,
    Department,
    Institution,
    Semester,
)


SEMESTER_CSV_COLUMNS = [
    "institution",
    "department",
    "course",
    "semester_number",
    "name",
    "is_active",
]


def read_semester_csv(uploaded_file):
    """
    Read a Semester CSV file using the common CSV reader.
    """

    return read_csv_file(
        uploaded_file,
        SEMESTER_CSV_COLUMNS,
    )


def validate_semester_rows(rows):
    """
    Validate Semester CSV rows.
    """

    seen = set()

    for row in rows:

        row_number = row["row_number"]

        institution_name = row[
            "institution"
        ].strip()

        department_name = row[
            "department"
        ].strip()

        course_name = row[
            "course"
        ].strip()

        semester_number = row[
            "semester_number"
        ].strip()

        name = row["name"].strip()

        is_active = row[
            "is_active"
        ].strip()

        # ----------------------------------------------
        # Required fields
        # ----------------------------------------------

        if not institution_name:
            raise ValueError(
                f"Row {row_number}: "
                "Institution is required."
            )

        if not department_name:
            raise ValueError(
                f"Row {row_number}: "
                "Department is required."
            )

        if not course_name:
            raise ValueError(
                f"Row {row_number}: "
                "Course is required."
            )

        if not semester_number:
            raise ValueError(
                f"Row {row_number}: "
                "Semester number is required."
            )

        if not name:
            raise ValueError(
                f"Row {row_number}: "
                "Semester name is required."
            )

        # ----------------------------------------------
        # Semester number validation
        # ----------------------------------------------

        try:

            semester_number_value = int(
                semester_number
            )

        except ValueError:

            raise ValueError(
                f"Row {row_number}: "
                "Semester number must be a whole number."
            )

        if semester_number_value < 1:

            raise ValueError(
                f"Row {row_number}: "
                "Semester number must be at least 1."
            )

        # ----------------------------------------------
        # Status validation
        # ----------------------------------------------

        if is_active not in (
            "0",
            "1",
        ):

            raise ValueError(
                f"Row {row_number}: "
                "is_active must be 0 or 1."
            )

        # ----------------------------------------------
        # Institution lookup
        # ----------------------------------------------

        try:

            institution = Institution.objects.get(
                name__iexact=institution_name
            )

        except Institution.DoesNotExist:

            raise ValueError(
                f"Row {row_number}: "
                f"Institution '{institution_name}' "
                "does not exist."
            )

        # ----------------------------------------------
        # Department lookup
        # ----------------------------------------------

        try:

            department = Department.objects.get(
                institution=institution,
                name__iexact=department_name,
            )

        except Department.DoesNotExist:

            raise ValueError(
                f"Row {row_number}: "
                f"Department '{department_name}' "
                f"does not exist in "
                f"'{institution.name}'."
            )

        # ----------------------------------------------
        # Course lookup
        # ----------------------------------------------

        try:

            course = Course.objects.get(
                department=department,
                name__iexact=course_name,
            )

        except Course.DoesNotExist:

            raise ValueError(
                f"Row {row_number}: "
                f"Course '{course_name}' "
                f"does not exist in "
                f"'{department.name}'."
            )

        # ----------------------------------------------
        # Duplicate rows inside CSV
        # ----------------------------------------------

        key = (
            course.pk,
            semester_number_value,
        )

        if key in seen:

            raise ValueError(
                f"Row {row_number}: "
                f"Semester {semester_number_value} "
                f"already appears for "
                f"course '{course.name}'."
            )

        seen.add(key)

        # ----------------------------------------------
        # Existing semester
        # ----------------------------------------------

        if Semester.objects.filter(
            course=course,
            semester_number=semester_number_value,
        ).exists():

            raise ValueError(
                f"Row {row_number}: "
                f"Semester {semester_number_value} "
                f"already exists for "
                f"course '{course.name}'."
            )

        # ----------------------------------------------
        # Existing semester name
        # ----------------------------------------------

        if Semester.objects.filter(
            course=course,
            name__iexact=name,
        ).exists():

            raise ValueError(
                f"Row {row_number}: "
                f"Semester '{name}' already exists "
                f"for course '{course.name}'."
            )


def create_semester_from_csv_row(row):
    """
    Create a Semester from a validated CSV row.
    """

    institution = Institution.objects.get(
        name__iexact=row["institution"].strip()
    )

    department = Department.objects.get(
        institution=institution,
        name__iexact=row["department"].strip(),
    )

    course = Course.objects.get(
        department=department,
        name__iexact=row["course"].strip(),
    )

    return Semester.objects.create(
        course=course,
        semester_number=int(
            row["semester_number"].strip()
        ),
        name=row["name"].strip(),
        is_active=(
            row["is_active"].strip() == "1"
        ),
    )


def generate_semester_csv_template():
    """
    Generate the fixed Semester CSV template.
    """

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        SEMESTER_CSV_COLUMNS
    )

    return output.getvalue()