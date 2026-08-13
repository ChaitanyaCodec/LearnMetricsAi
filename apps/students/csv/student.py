"""
Student CSV import logic.

This module contains Student-specific CSV validation
and creation logic.

The transaction itself is handled by service.py.
"""

import csv
import io
import secrets
from datetime import datetime

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from apps.accounts.models import User

from ..models import Student
from .service import (
    StudentCSVImportError,
    import_student_rows,
)


EXPECTED_COLUMNS = (
    "email",
    "first_name",
    "last_name",
    "phone_number",
    "student_id",
    "admission_date",
)


def read_student_csv(uploaded_file):
    """
    Read and validate the structure of a Student CSV file.

    Returns:
        list[dict]: Cleaned CSV rows.
    """

    if not uploaded_file.name.lower().endswith(".csv"):
        raise StudentCSVImportError(
            "Please upload a CSV file."
        )

    content = uploaded_file.read()

    try:
        decoded = content.decode("utf-8-sig")

    except UnicodeDecodeError as exc:
        raise StudentCSVImportError(
            "CSV file must use UTF-8 encoding."
        ) from exc

    reader = csv.DictReader(
        io.StringIO(decoded)
    )

    if reader.fieldnames is None:
        raise StudentCSVImportError(
            "CSV file is empty or has no header row."
        )

    columns = tuple(
        column.strip()
        for column in reader.fieldnames
    )

    if columns != EXPECTED_COLUMNS:
        raise StudentCSVImportError(
            "Invalid CSV columns. "
            f"Expected: {', '.join(EXPECTED_COLUMNS)}"
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

    if not rows:
        raise StudentCSVImportError(
            "CSV file does not contain any data rows."
        )

    return rows


def validate_student_rows(rows):
    """
    Validate all Student CSV rows before database creation.

    Returns:
        list[dict]: Validated rows.
    """

    errors = []

    seen_emails = set()
    seen_student_ids = set()

    for row in rows:

        row_number = row["row_number"]

        email = row["email"].strip().lower()
        first_name = row["first_name"].strip()
        last_name = row["last_name"].strip()
        phone_number = row["phone_number"].strip()
        student_id = row["student_id"].strip()
        admission_date = row["admission_date"].strip()

        # -----------------------------
        # Required fields
        # -----------------------------

        if not email:
            errors.append(
                f"Row {row_number}: Email is required."
            )

        if not first_name:
            errors.append(
                f"Row {row_number}: First name is required."
            )

        if not last_name:
            errors.append(
                f"Row {row_number}: Last name is required."
            )

        if not student_id:
            errors.append(
                f"Row {row_number}: Student ID is required."
            )

        # -----------------------------
        # Email validation
        # -----------------------------

        if email:

            try:
                validate_email(email)

            except ValidationError:
                errors.append(
                    f"Row {row_number}: "
                    f"Invalid email address."
                )

        # -----------------------------
        # Duplicate email inside CSV
        # -----------------------------

        if email:

            if email in seen_emails:
                errors.append(
                    f"Row {row_number}: "
                    f"Duplicate email '{email}' "
                    f"inside CSV."
                )

            seen_emails.add(email)

        # -----------------------------
        # Duplicate student ID inside CSV
        # -----------------------------

        if student_id:

            normalized_student_id = (
                student_id.lower()
            )

            if normalized_student_id in seen_student_ids:
                errors.append(
                    f"Row {row_number}: "
                    f"Duplicate student ID "
                    f"'{student_id}' inside CSV."
                )

            seen_student_ids.add(
                normalized_student_id
            )

        # -----------------------------
        # Existing User
        # -----------------------------

        if email and User.objects.filter(
            email__iexact=email
        ).exists():

            errors.append(
                f"Row {row_number}: "
                f"A user with email "
                f"'{email}' already exists."
            )

        # -----------------------------
        # Existing Student
        # -----------------------------

        if student_id and Student.objects.filter(
            student_id=student_id
        ).exists():

            errors.append(
                f"Row {row_number}: "
                f"Student ID "
                f"'{student_id}' already exists."
            )

        # -----------------------------
        # Admission date
        # -----------------------------

        parsed_admission_date = None

        if admission_date:

            try:
                parsed_admission_date = (
                    datetime.strptime(
                        admission_date,
                        "%Y-%m-%d",
                    ).date()
                )

            except ValueError:
                errors.append(
                    f"Row {row_number}: "
                    f"Invalid admission date "
                    f"'{admission_date}'. "
                    f"Expected YYYY-MM-DD."
                )

        # Store normalized values
        row["email"] = email
        row["first_name"] = first_name
        row["last_name"] = last_name
        row["phone_number"] = phone_number
        row["student_id"] = student_id
        row["admission_date"] = (
            parsed_admission_date
        )

    if errors:
        raise StudentCSVImportError(
            errors
        )

    return rows


def create_student_from_row(row):
    """
    Create one User and Student profile.

    This function is called only after every CSV row
    has passed validation.
    """

    temporary_password = secrets.token_urlsafe(
        12
    )

    user = User.objects.create_user(
        email=row["email"],
        password=temporary_password,
        first_name=row["first_name"],
        last_name=row["last_name"],
        phone_number=row["phone_number"],
        role=User.Roles.STUDENT,
        is_active=True,
    )

    student = Student.objects.create(
        user=user,
        student_id=row["student_id"],
        admission_date=row["admission_date"],
    )

    return {
        "student": student,
        "temporary_password": temporary_password,
    }


def import_students(uploaded_file):
    """
    Complete Student CSV import workflow.

    All rows are read and validated before any
    database records are created.
    """

    rows = read_student_csv(
        uploaded_file
    )

    rows = validate_student_rows(
        rows
    )

    return import_student_rows(
        rows,
        create_student_from_row,
    )