"""
Common CSV import utilities for the Academics module.

This module contains logic shared by all academic CSV imports.

Entity-specific validation and database creation remain
inside the corresponding entity modules.
"""

from __future__ import annotations

import csv
import io

from django.db import transaction


class CSVImportError(Exception):
    """
    Base exception for CSV import errors.
    """

    pass


def read_csv_file(
    uploaded_file,
    expected_columns,
):
    """
    Read a CSV file and validate its column structure.

    Returns:
        list[dict]: Parsed CSV rows.
    """

    # ------------------------------------------------------
    # File extension
    # ------------------------------------------------------

    if not uploaded_file.name.lower().endswith(".csv"):

        raise CSVImportError(
            "Please upload a CSV file."
        )

    # ------------------------------------------------------
    # Read file
    # ------------------------------------------------------

    content = uploaded_file.read()

    try:

        decoded = content.decode("utf-8-sig")

    except UnicodeDecodeError as exc:

        raise CSVImportError(
            "CSV file must use UTF-8 encoding."
        ) from exc

    # ------------------------------------------------------
    # CSV reader
    # ------------------------------------------------------

    reader = csv.DictReader(
        io.StringIO(decoded)
    )

    if reader.fieldnames is None:

        raise CSVImportError(
            "CSV file is empty or has no header row."
        )

    # ------------------------------------------------------
    # Validate columns
    # ------------------------------------------------------

    columns = [
        column.strip()
        for column in reader.fieldnames
    ]

    expected_columns = list(
        expected_columns
    )

    if columns != expected_columns:

        raise CSVImportError(
            "Invalid CSV columns. "
            f"Expected: {', '.join(expected_columns)}"
        )

    # ------------------------------------------------------
    # Read rows
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # Empty data validation
    # ------------------------------------------------------

    if not rows:

        raise CSVImportError(
            "CSV file does not contain any data rows."
        )

    return rows


def import_rows(
    rows,
    create_callback,
):
    """
    Import validated rows atomically.

    Args:
        rows:
            Fully validated CSV rows.

        create_callback:
            Entity-specific function responsible
            for creating one database record.

    Returns:
        int:
            Number of imported records.
    """

    imported_count = 0

    with transaction.atomic():

        for row in rows:

            create_callback(row)

            imported_count += 1

    return imported_count

def validate_required_fields(
    row,
    required_fields,
    labels=None,
):
    """
    Validate required CSV fields.

    Args:
        row:
            Current CSV row.

        required_fields:
            Field names that must contain values.

        labels:
            Optional human-readable field labels.

    Raises:
        ValueError:
            If a required field is empty.
    """

    row_number = row["row_number"]

    labels = labels or {}

    for field in required_fields:

        value = row.get(field, "").strip()

        if not value:

            label = labels.get(
                field,
                field.replace("_", " ").title(),
            )

            raise ValueError(
                f"Row {row_number}: "
                f"{label} is required."
            )


def validate_active_status(row):
    """
    Validate the common is_active CSV field.
    """

    row_number = row["row_number"]

    value = row.get(
        "is_active",
        "",
    ).strip()

    if value not in ("0", "1"):

        raise ValueError(
            f"Row {row_number}: "
            "is_active must be 0 or 1."
        )


def generate_csv_template(columns):
    """
    Generate a CSV template containing
    the supplied column headers.
    """

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(columns)

    return output.getvalue()