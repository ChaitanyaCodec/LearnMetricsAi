"""
Course CSV import functionality.
"""

from __future__ import annotations

from .service import read_csv_file

from ..models import (
    Course,
    Department,
    Institution,
)


COURSE_CSV_COLUMNS = [
    "institution",
    "department",
    "name",
    "code",
    "duration",
    "description",
    "is_active",
]


def read_course_csv(uploaded_file):
    """
    Read a Course CSV file using the common CSV reader.
    """

    return read_csv_file(
        uploaded_file,
        COURSE_CSV_COLUMNS,
    )


def validate_course_rows(rows):
    """
    Validate Course CSV rows.
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

        name = row["name"].strip()

        code = row["code"].strip()

        duration = row["duration"].strip()

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

        if not name:

            raise ValueError(
                f"Row {row_number}: "
                "Course name is required."
            )

        if not code:

            raise ValueError(
                f"Row {row_number}: "
                "Course code is required."
            )

        # ----------------------------------------------
        # Duration validation
        # ----------------------------------------------

        try:

            duration_value = int(duration)

        except ValueError:

            raise ValueError(
                f"Row {row_number}: "
                "Duration must be a whole number."
            )

        if duration_value < 1:

            raise ValueError(
                f"Row {row_number}: "
                "Duration must be at least 1 year."
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
        # Duplicate rows inside CSV
        # ----------------------------------------------

        key = (
            department.pk,
            name.lower(),
        )

        if key in seen:

            raise ValueError(
                f"Row {row_number}: "
                f"Duplicate course '{name}' "
                "for the same department."
            )

        seen.add(key)

        # ----------------------------------------------
        # Existing course name
        # ----------------------------------------------

        if Course.objects.filter(
            department=department,
            name__iexact=name,
        ).exists():

            raise ValueError(
                f"Row {row_number}: "
                f"Course '{name}' already exists "
                f"in '{department.name}'."
            )

        # ----------------------------------------------
        # Existing course code
        # ----------------------------------------------

        if Course.objects.filter(
            department=department,
            code__iexact=code,
        ).exists():

            raise ValueError(
                f"Row {row_number}: "
                f"Course code '{code}' already exists "
                f"in '{department.name}'."
            )


def create_course_from_csv_row(row):
    """
    Create a Course from a validated CSV row.
    """

    institution = Institution.objects.get(
        name__iexact=row["institution"].strip()
    )

    department = Department.objects.get(
        institution=institution,
        name__iexact=row["department"].strip(),
    )

    return Course.objects.create(
        department=department,
        name=row["name"].strip(),
        code=row["code"].strip(),
        duration=int(row["duration"].strip()),
        description=row["description"].strip(),
        is_active=(
            row["is_active"].strip() == "1"
        ),
    )


def generate_course_csv_template():
    """
    Generate the fixed Course CSV template.
    """

    import csv
    import io

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        COURSE_CSV_COLUMNS
    )

    return output.getvalue()