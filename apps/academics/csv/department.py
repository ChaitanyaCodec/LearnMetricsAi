"""
Department CSV import functionality.
"""

from __future__ import annotations

from .service import (
    generate_csv_template,
    read_csv_file,
    validate_active_status,
    validate_required_fields,
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

        validate_required_fields(
            row,
            (
                "institution",
                "name",
                "code",
            ),
            {
                "institution": "Institution",
                "name": "Department name",
                "code": "Department code",
            },
        )

        validate_active_status(row)
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

    return generate_csv_template(
        DEPARTMENT_CSV_COLUMNS
    )