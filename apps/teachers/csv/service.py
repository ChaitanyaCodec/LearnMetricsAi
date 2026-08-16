"""
CSV import service for Teacher records.

Responsible for:
- Reading and validating teacher CSV data.
- Validating the complete file before writing.
- Creating User + Teacher records atomically.
- Generating temporary passwords.
"""

from __future__ import annotations

import csv
import io
import secrets
import string
from datetime import datetime

from django.db import transaction

from apps.accounts.models import User

from ..models import Teacher


class TeacherCSVImportError(Exception):
    """
    Raised when the teacher CSV cannot be imported.
    """

    pass


class TeacherCSVImportService:
    """
    Handles bulk creation of Teacher accounts and profiles.
    """

    REQUIRED_COLUMNS = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "employee_id",
        "joining_date",
    )

    DATE_FORMAT = "%Y-%m-%d"

    # ======================================================
    # Public API
    # ======================================================

    @classmethod
    @transaction.atomic
    def import_csv(cls, uploaded_file):
        """
        Validate and import the complete CSV.

        No records are created if any validation error
        occurs.
        """

        rows = cls._read_csv(uploaded_file)

        cls._validate_headers(rows)

        errors = cls._validate_rows(rows)

        if errors:
            raise TeacherCSVImportError(errors)

        return cls._create_teachers(rows)

    # ======================================================
    # CSV Reading
    # ======================================================

    @classmethod
    def _read_csv(cls, uploaded_file):
        """
        Read uploaded CSV as UTF-8 text.
        """

        try:
            raw_data = uploaded_file.read()

            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode("utf-8-sig")

            else:
                raw_data = raw_data.lstrip("\ufeff")

        except UnicodeDecodeError:
            raise TeacherCSVImportError(
                [
                    "The CSV file must use UTF-8 encoding."
                ]
            )

        except Exception:
            raise TeacherCSVImportError(
                [
                    "Unable to read the uploaded CSV file."
                ]
            )

        if not raw_data.strip():
            raise TeacherCSVImportError(
                [
                    "The uploaded CSV file is empty."
                ]
            )

        reader = csv.DictReader(
            io.StringIO(raw_data)
        )

        return list(reader)

    # ======================================================
    # Header Validation
    # ======================================================

    @classmethod
    def _validate_headers(cls, rows):
        """
        Validate that all required columns exist.
        """

        if not rows:
            raise TeacherCSVImportError(
                [
                    "The CSV file does not contain any data rows."
                ]
            )

        # DictReader fieldnames are not available after
        # converting directly to a list, so this validation
        # is performed against the keys of the first row.
        headers = set(rows[0].keys())

        missing = [
            column
            for column in cls.REQUIRED_COLUMNS
            if column not in headers
        ]

        if missing:
            raise TeacherCSVImportError(
                [
                    "Missing required column(s): "
                    + ", ".join(missing)
                ]
            )

        unexpected = [
            column
            for column in headers
            if column not in cls.REQUIRED_COLUMNS
        ]

        if unexpected:
            raise TeacherCSVImportError(
                [
                    "Unexpected column(s): "
                    + ", ".join(
                        str(column)
                        for column in unexpected
                        if column is not None
                    )
                ]
            )

    # ======================================================
    # Row Validation
    # ======================================================

    @classmethod
    def _validate_rows(cls, rows):
        """
        Validate every row before any database write.
        """

        errors = []

        emails = set()
        employee_ids = set()

        for row_number, row in enumerate(
            rows,
            start=2,
        ):

            email = (
                row.get("email") or ""
            ).strip().lower()

            first_name = (
                row.get("first_name") or ""
            ).strip()

            last_name = (
                row.get("last_name") or ""
            ).strip()

            employee_id = (
                row.get("employee_id") or ""
            ).strip()

            joining_date = (
                row.get("joining_date") or ""
            ).strip()

            # ----------------------------------------------
            # Required fields
            # ----------------------------------------------

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

            if not employee_id:
                errors.append(
                    f"Row {row_number}: Employee ID is required."
                )

            # ----------------------------------------------
            # Duplicate values inside CSV
            # ----------------------------------------------

            if email:

                if email in emails:
                    errors.append(
                        f"Row {row_number}: Duplicate email "
                        f"'{email}' in CSV."
                    )

                emails.add(email)

            if employee_id:

                if employee_id in employee_ids:
                    errors.append(
                        f"Row {row_number}: Duplicate employee ID "
                        f"'{employee_id}' in CSV."
                    )

                employee_ids.add(employee_id)

            # ----------------------------------------------
            # Database duplicates
            # ----------------------------------------------

            if email and User.objects.filter(
                email=email
            ).exists():

                errors.append(
                    f"Row {row_number}: Email "
                    f"'{email}' already exists."
                )

            if employee_id and Teacher.objects.filter(
                employee_id=employee_id
            ).exists():

                errors.append(
                    f"Row {row_number}: Employee ID "
                    f"'{employee_id}' already exists."
                )

            # ----------------------------------------------
            # Joining date
            # ----------------------------------------------

            if joining_date:

                try:
                    datetime.strptime(
                        joining_date,
                        cls.DATE_FORMAT,
                    )

                except ValueError:

                    errors.append(
                        f"Row {row_number}: Invalid joining date "
                        f"'{joining_date}'. Expected YYYY-MM-DD."
                    )

        return errors

    # ======================================================
    # Teacher Creation
    # ======================================================

    @classmethod
    def _create_teachers(cls, rows):
        """
        Create all User and Teacher records.
        """

        results = []

        for row in rows:

            email = (
                row["email"]
                .strip()
                .lower()
            )

            first_name = (
                row["first_name"]
                .strip()
            )

            last_name = (
                row["last_name"]
                .strip()
            )

            phone_number = (
                row.get("phone_number") or ""
            ).strip()

            employee_id = (
                row["employee_id"]
                .strip()
            )

            joining_date_value = (
                row.get("joining_date") or ""
            ).strip()

            joining_date = None

            if joining_date_value:
                joining_date = datetime.strptime(
                    joining_date_value,
                    cls.DATE_FORMAT,
                ).date()

            temporary_password = (
                cls._generate_password()
            )

            user = User.objects.create_user(
                email=email,
                password=temporary_password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                role=User.Roles.TEACHER,
            )

            teacher = Teacher.objects.create(
                user=user,
                employee_id=employee_id,
                joining_date=joining_date,
            )

            results.append(
                {
                    "teacher_id": teacher.pk,
                    "employee_id": teacher.employee_id,
                    "name": (
                        f"{user.first_name} "
                        f"{user.last_name}"
                    ),
                    "email": user.email,
                    "temporary_password": (
                        temporary_password
                    ),
                }
            )

        return results

    # ======================================================
    # Password Generation
    # ======================================================

    @staticmethod
    def _generate_password(length=12):
        """
        Generate a temporary password.
        """

        alphabet = (
            string.ascii_letters
            + string.digits
            + "!@#$%"
        )

        return "".join(
            secrets.choice(alphabet)
            for _ in range(length)
        )