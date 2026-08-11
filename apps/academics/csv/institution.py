"""
Institution CSV import utilities.

Handles:
- CSV structure validation
- CSV row parsing
- Institution import preparation
"""

from .service import (
    CSVImportError,
    read_csv_file,
    generate_csv_template,
    import_rows
   
)
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email

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
def create_institution_from_csv_row(row):
    """
    Create an Institution from a validated CSV row.
    """

    return Institution.objects.create(
        name=row["name"],
        short_name=row["short_name"],
        email=row["email"],
        phone_number=row["phone_number"],
        website=row["website"],
        address=row["address"],
        is_active=(
            row["is_active"] == "1"
        ),
    )

def read_institution_csv(uploaded_file):
    """
    Read an Institution CSV using the common CSV engine.
    """

    return read_csv_file(
        uploaded_file,
        INSTITUTION_CSV_COLUMNS,
    )

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
    """

    return generate_csv_template(
        INSTITUTION_CSV_COLUMNS
    )