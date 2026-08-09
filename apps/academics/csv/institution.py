"""
Institution CSV import utilities.

Handles:
- CSV structure validation
- CSV row parsing
- Institution import preparation
"""

import csv
import io
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from apps.academics.models import Institution

INSTITUTION_CSV_COLUMNS = [
    "name",
    "short_name",
    "email",
    "phone_number",
    "website",
    "address",
    "is_active",
]


def read_institution_csv(uploaded_file):
    """
    Read and validate an Institution CSV file.

    Returns:
        list[dict]: Parsed CSV rows.
    """

    if not uploaded_file.name.lower().endswith(".csv"):
        raise ValueError(
            "Please upload a CSV file."
        )

    content = uploaded_file.read()

    try:
        decoded = content.decode("utf-8-sig")

    except UnicodeDecodeError as exc:
        raise ValueError(
            "CSV file must use UTF-8 encoding."
        ) from exc

    reader = csv.DictReader(
        io.StringIO(decoded)
    )

    if reader.fieldnames is None:
        raise ValueError(
            "CSV file is empty or has no header row."
        )

    columns = [
        column.strip()
        for column in reader.fieldnames
    ]

    if columns != INSTITUTION_CSV_COLUMNS:
        raise ValueError(
            "Invalid CSV columns. "
            f"Expected: {', '.join(INSTITUTION_CSV_COLUMNS)}"
        )

    rows = []

    for row_number, row in enumerate(
        reader,
        start=2,
    ):

        cleaned_row = {
            key: (
                value.strip()
                if value is not None
                else ""
            )
            for key, value in row.items()
        }

        cleaned_row["row_number"] = row_number
        rows.append(cleaned_row)

    return rows

def validate_institution_rows(rows):
    """
    Validate Institution CSV rows.

    No database records are created here.

    Returns:
        list[dict]: Validated rows.

    Raises:
        ValueError: If one or more rows are invalid.
    """

    errors = []

    seen_names = set()
    seen_short_names = set()

    url_validator = URLValidator()

    for row in rows:

        row_number = row["row_number"]

        name = row["name"]
        short_name = row["short_name"]
        email = row["email"]
        phone_number = row["phone_number"]
        website = row["website"]
        address = row["address"]
        is_active = row["is_active"]

        # --------------------------------------------------
        # Required fields
        # --------------------------------------------------

        if not name:
            errors.append(
                f"Row {row_number}: Institution name is required."
            )

        if not short_name:
            errors.append(
                f"Row {row_number}: Short name is required."
            )

        if not email:
            errors.append(
                f"Row {row_number}: Email is required."
            )

        if not phone_number:
            errors.append(
                f"Row {row_number}: Phone number is required."
            )

        # --------------------------------------------------
        # Duplicate rows inside CSV
        # --------------------------------------------------

        if name:

            normalized_name = name.casefold()

            if normalized_name in seen_names:
                errors.append(
                    f"Row {row_number}: Duplicate institution "
                    f"name '{name}' in CSV."
                )

            seen_names.add(normalized_name)

        if short_name:

            normalized_short_name = (
                short_name.casefold()
            )

            if normalized_short_name in seen_short_names:
                errors.append(
                    f"Row {row_number}: Duplicate short name "
                    f"'{short_name}' in CSV."
                )

            seen_short_names.add(
                normalized_short_name
            )

        # --------------------------------------------------
        # Existing database records
        # --------------------------------------------------

        if name and Institution.objects.filter(
            name__iexact=name
        ).exists():

            errors.append(
                f"Row {row_number}: Institution "
                f"'{name}' already exists."
            )

        if short_name and Institution.objects.filter(
            short_name__iexact=short_name
        ).exists():

            errors.append(
                f"Row {row_number}: Short name "
                f"'{short_name}' already exists."
            )

        # --------------------------------------------------
        # Email validation
        # --------------------------------------------------

        if email:

            from django.core.validators import (
                validate_email,
            )

            try:

                validate_email(email)

            except ValidationError:

                errors.append(
                    f"Row {row_number}: Invalid email "
                    f"address '{email}'."
                )

        # --------------------------------------------------
        # Website validation
        # --------------------------------------------------

        if website:

            try:

                url_validator(website)

            except ValidationError:

                errors.append(
                    f"Row {row_number}: Invalid website "
                    f"URL '{website}'."
                )

        # --------------------------------------------------
        # Active status validation
        # --------------------------------------------------

        if is_active not in ("0", "1"):

            errors.append(
                f"Row {row_number}: is_active must be "
                f"'1' or '0'."
            )

    if errors:

        raise ValueError(
            "\n".join(errors)
        )

    return rows

def generate_institution_csv_template():
    """
    Generate the fixed Institution CSV template.

    Returns:
        str: CSV content.
    """

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        INSTITUTION_CSV_COLUMNS
    )

    return output.getvalue()