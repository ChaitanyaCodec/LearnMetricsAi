"""
Teacher CSV import utilities.

Handles:
- CSV structure validation
- CSV row parsing
- Teacher row validation
- Teacher creation preparation
- Teacher CSV template generation
"""

import csv
import io

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from apps.accounts.models import User

from ..models import Teacher


TEACHER_CSV_COLUMNS = [
    "email",
    "first_name",
    "last_name",
    "phone_number",
    "employee_id",
    "joining_date",
]


def read_teacher_csv(uploaded_file):
    """
    Read a Teacher CSV using the common CSV engine.
    """

    from .service import read_csv_file

    return read_csv_file(
        uploaded_file,
        TEACHER_CSV_COLUMNS,
    )


def validate_teacher_rows(rows):
    """
    Validate Teacher CSV rows.

    No database records are created here.

    Raises:
        ValueError: If one or more rows are invalid.
    """

    errors = []

    seen_emails = set()
    seen_employee_ids = set()

    for row in rows:

        row_number = row["row_number"]

        email = row["email"].strip()
        first_name = row["first_name"].strip()
        last_name = row["last_name"].strip()
        phone_number = row["phone_number"].strip()
        employee_id = row["employee_id"].strip()
        joining_date = row["joining_date"].strip()

        # --------------------------------------------------
        # Required fields
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Email validation
        # --------------------------------------------------

        if email:

            try:
                validate_email(email)

            except ValidationError:

                errors.append(
                    f"Row {row_number}: "
                    f"Invalid email address '{email}'."
                )

        # --------------------------------------------------
        # Duplicate email inside CSV
        # --------------------------------------------------

        if email:

            normalized_email = email.casefold()

            if normalized_email in seen_emails:

                errors.append(
                    f"Row {row_number}: Duplicate email "
                    f"'{email}' in CSV."
                )

            seen_emails.add(
                normalized_email
            )

        # --------------------------------------------------
        # Duplicate employee ID inside CSV
        # --------------------------------------------------

        if employee_id:

            normalized_employee_id = (
                employee_id.casefold()
            )

            if normalized_employee_id in seen_employee_ids:

                errors.append(
                    f"Row {row_number}: Duplicate employee ID "
                    f"'{employee_id}' in CSV."
                )

            seen_employee_ids.add(
                normalized_employee_id
            )

        # --------------------------------------------------
        # Existing User email
        # --------------------------------------------------

        if email:

            if User.objects.filter(
                email__iexact=email
            ).exists():

                errors.append(
                    f"Row {row_number}: Email "
                    f"'{email}' already exists."
                )

        # --------------------------------------------------
        # Existing Teacher employee ID
        # --------------------------------------------------

        if employee_id:

            if Teacher.objects.filter(
                employee_id__iexact=employee_id
            ).exists():

                errors.append(
                    f"Row {row_number}: Employee ID "
                    f"'{employee_id}' already exists."
                )

        # --------------------------------------------------
        # Joining date
        # --------------------------------------------------

        if joining_date:

            from datetime import datetime

            try:

                datetime.strptime(
                    joining_date,
                    "%Y-%m-%d",
                )

            except ValueError:

                errors.append(
                    f"Row {row_number}: Invalid joining date "
                    f"'{joining_date}'. Expected YYYY-MM-DD."
                )

    if errors:

        raise ValueError(
            "\n".join(errors)
        )


def create_teacher_from_csv_row(row):
    """
    Create a Teacher and its associated User
    from a validated CSV row.
    """

    from datetime import datetime

    email = row["email"].strip().lower()

    first_name = row["first_name"].strip()

    last_name = row["last_name"].strip()

    phone_number = row["phone_number"].strip()

    employee_id = row["employee_id"].strip()

    joining_date_value = (
        row["joining_date"].strip()
    )

    joining_date = None

    if joining_date_value:

        joining_date = datetime.strptime(
            joining_date_value,
            "%Y-%m-%d",
        ).date()

    # Temporary password generation will be handled
    # by the Teacher import flow.
    #
    # We are deliberately not finalizing that part
    # until the common import transaction is connected.

    raise NotImplementedError(
        "Teacher CSV creation will be connected "
        "to the Teacher service in the next step."
    )


def generate_teacher_csv_template():
    """
    Generate the fixed Teacher CSV template.
    """

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        TEACHER_CSV_COLUMNS
    )

    return output.getvalue()