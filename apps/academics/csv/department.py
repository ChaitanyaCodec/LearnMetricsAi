"""
Department CSV import functionality.
"""

from __future__ import annotations

from .service import (
    read_csv_file,
)

from ..models import (
    Department,
    Institution,
)
import csv
import io

DEPARTMENT_CSV_COLUMNS = [
    "institution",
    "name",
    "code",
    "description",
    "is_active",
]


def read_department_csv(uploaded_file):
    """
    Read a Department CSV file using the
    common CSV reader.
    """

    return read_csv_file(
        uploaded_file,
        DEPARTMENT_CSV_COLUMNS,
    )


def validate_department_rows(rows):
    """
    Validate Department CSV rows.
    """

    seen = set()

    for row in rows:

        row_number = row["row_number"]

        institution_name = row[
            "institution"
        ].strip()

        name = row["name"].strip()

        code = row["code"].strip()

        is_active = row[
            "is_active"
        ].strip()

        if not institution_name:

            raise ValueError(
                f"Row {row_number}: "
                "Institution is required."
            )

        if not name:

            raise ValueError(
                f"Row {row_number}: "
                "Department name is required."
            )

        if not code:

            raise ValueError(
                f"Row {row_number}: "
                "Department code is required."
            )

        if is_active not in (
            "0",
            "1",
        ):

            raise ValueError(
                f"Row {row_number}: "
                "is_active must be 0 or 1."
            )

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

        key = (
            institution.pk,
            name.lower(),
        )

        if key in seen:

            raise ValueError(
                f"Row {row_number}: "
                f"Duplicate department '{name}' "
                "for the same institution."
            )

        seen.add(key)

        if Department.objects.filter(
            institution=institution,
            name__iexact=name,
        ).exists():

            raise ValueError(
                f"Row {row_number}: "
                f"Department '{name}' already "
                f"exists in '{institution.name}'."
            )

        if Department.objects.filter(
            institution=institution,
            code__iexact=code,
        ).exists():

            raise ValueError(
                f"Row {row_number}: "
                f"Department code '{code}' already "
                f"exists in '{institution.name}'."
            )


def create_department_from_csv_row(row):
    """
    Create a Department from a validated CSV row.
    """

    institution = Institution.objects.get(
        name__iexact=row["institution"].strip()
    )

    return Department.objects.create(
        institution=institution,
        name=row["name"].strip(),
        code=row["code"].strip(),
        description=row["description"].strip(),
        is_active=(
            row["is_active"].strip() == "1"
        ),
    )

def generate_department_csv_template():
    """
    Generate the fixed Department CSV template.
    """

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        DEPARTMENT_CSV_COLUMNS
    )

    return output.getvalue()