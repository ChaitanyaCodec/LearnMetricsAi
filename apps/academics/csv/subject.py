"""
Subject CSV import functionality.
"""

from __future__ import annotations

import csv
import io

from .service import (
    generate_csv_template,
    read_csv_file,
    validate_active_status,
    validate_required_fields,
)

from ..models import (
    Institution,
    Department,
    Course,
    Semester,
    Subject,
)


SUBJECT_CSV_COLUMNS = [
    "institution",
    "department",
    "course",
    "semester_number",
    "subject_code",
    "name",
    "credits",
    "description",
    "is_active",
]


def read_subject_csv(uploaded_file):
    """
    Read a Subject CSV file using the common CSV reader.
    """

    return read_csv_file(
        uploaded_file,
        SUBJECT_CSV_COLUMNS,
    )


def validate_subject_rows(rows):
    """
    Validate Subject CSV rows.
    """

    seen_codes = set()
    seen_names = set()

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

        subject_code = row[
            "subject_code"
        ].strip()

        name = row[
            "name"
        ].strip()

        credits = row[
            "credits"
        ].strip()

        is_active = row[
            "is_active"
        ].strip()

        # ----------------------------------------------
        # Required fields
        # ----------------------------------------------
        validate_required_fields(
            row,
            (
                "institution",
                "department",
                "course",
                "semester_number",
                "subject_code",
                "name",
            ),
            {
                "institution": "Institution",
                "department": "Department",
                "course": "Course",
                "semester_number": "Semester number",
                "subject_code": "Subject code",
                "name": "Subject name",
            },
        )

        validate_active_status(row)
        # ----------------------------------------------
        # Semester number
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
        # Credits
        # ----------------------------------------------

        try:

            credits_value = int(
                credits
            )

        except ValueError:

            raise ValueError(
                f"Row {row_number}: "
                "Credits must be a whole number."
            )

        if credits_value < 1:

            raise ValueError(
                f"Row {row_number}: "
                "Credits must be at least 1."
            )

        # ----------------------------------------------
        # Status
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
        # Institution
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
        # Department
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
        # Course
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
        # Semester
        # ----------------------------------------------

        try:

            semester = Semester.objects.get(
                course=course,
                semester_number=semester_number_value,
            )

        except Semester.DoesNotExist:

            raise ValueError(
                f"Row {row_number}: "
                f"Semester {semester_number_value} "
                f"does not exist for "
                f"course '{course.name}'."
            )

        # ----------------------------------------------
        # Duplicate CSV rows
        # ----------------------------------------------

        code_key = (
            semester.pk,
            subject_code.lower(),
        )

        name_key = (
            semester.pk,
            name.lower(),
        )

        if code_key in seen_codes:

            raise ValueError(
                f"Row {row_number}: "
                f"Duplicate subject code "
                f"'{subject_code}' in the same semester."
            )

        if name_key in seen_names:

            raise ValueError(
                f"Row {row_number}: "
                f"Duplicate subject "
                f"'{name}' in the same semester."
            )

        seen_codes.add(code_key)
        seen_names.add(name_key)

        # ----------------------------------------------
        # Existing subject code
        # ----------------------------------------------

        if Subject.objects.filter(
            semester=semester,
            code__iexact=subject_code,
        ).exists():

            raise ValueError(
                f"Row {row_number}: "
                f"Subject code '{subject_code}' "
                f"already exists in "
                f"'{semester.name}'."
            )

        # ----------------------------------------------
        # Existing subject name
        # ----------------------------------------------

        if Subject.objects.filter(
            semester=semester,
            name__iexact=name,
        ).exists():

            raise ValueError(
                f"Row {row_number}: "
                f"Subject '{name}' already exists "
                f"in '{semester.name}'."
            )


def create_subject_from_csv_row(row):
    """
    Create a Subject from a validated CSV row.
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

    semester = Semester.objects.get(
        course=course,
        semester_number=int(
            row["semester_number"].strip()
        ),
    )

    return Subject.objects.create(
        semester=semester,
        code=row["subject_code"].strip(),
        name=row["name"].strip(),
        credits=int(
            row["credits"].strip()
        ),
        description=row["description"].strip(),
        is_active=(
            row["is_active"].strip() == "1"
        ),
    )

def generate_subject_csv_template():
    """
    Generate the fixed Subject CSV template.
    """

    return generate_csv_template(
        SUBJECT_CSV_COLUMNS
    )