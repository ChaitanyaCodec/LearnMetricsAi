import csv
import io

from django.db import transaction

from apps.academics.models import (
    Institution,
    Department,
    Course,
    Semester,
    Subject,
)

from ..models import Teacher, TeachingAssignment
from ..services import TeacherService


ASSIGNMENT_CSV_COLUMNS = [
    "employee_id",
    "institution_short_name",
    "department_code",
    "course_code",
    "semester_number",
    "subject_code",
]


class TeacherAssignmentCSVImportError(Exception):
    """Raised when assignment CSV validation fails."""

    pass


def read_assignment_csv(uploaded_file):
    """
    Read the uploaded CSV and return normalized rows.
    """

    try:
        content = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TeacherAssignmentCSVImportError(
            "The CSV file must be UTF-8 encoded."
        ) from exc

    reader = csv.DictReader(
        io.StringIO(content)
    )

    if not reader.fieldnames:
        raise TeacherAssignmentCSVImportError(
            "The CSV file is empty or has no header."
        )

    headers = [
        header.strip()
        for header in reader.fieldnames
    ]

    if headers != ASSIGNMENT_CSV_COLUMNS:
        raise TeacherAssignmentCSVImportError(
            "Invalid CSV columns. Expected: "
            + ", ".join(ASSIGNMENT_CSV_COLUMNS)
        )

    rows = []

    for row_number, row in enumerate(
        reader,
        start=2,
    ):
        rows.append(
            {
                "row_number": row_number,
                "employee_id": (
                    row.get("employee_id") or ""
                ).strip(),
                "institution_short_name": (
                    row.get("institution_short_name") or ""
                ).strip(),
                "department_code": (
                    row.get("department_code") or ""
                ).strip(),
                "course_code": (
                    row.get("course_code") or ""
                ).strip(),
                "semester_number": (
                    row.get("semester_number") or ""
                ).strip(),
                "subject_code": (
                    row.get("subject_code") or ""
                ).strip(),
            }
        )

    if not rows:
        raise TeacherAssignmentCSVImportError(
            "The CSV file contains no data rows."
        )

    return rows


def validate_assignment_rows(rows):
    """
    Validate every CSV row before creating assignments.
    """

    errors = []
    validated_rows = []
    seen_assignments = set()

    for row in rows:

        row_number = row["row_number"]

        employee_id = row["employee_id"]
        institution_short_name = (
            row["institution_short_name"]
        )
        department_code = row["department_code"]
        course_code = row["course_code"]
        semester_number = row["semester_number"]
        subject_code = row["subject_code"]

        # --------------------------------------------------
        # Required fields
        # --------------------------------------------------

        required_fields = {
            "employee_id": employee_id,
            "institution_short_name": (
                institution_short_name
            ),
            "department_code": department_code,
            "course_code": course_code,
            "semester_number": semester_number,
            "subject_code": subject_code,
        }

        missing_fields = [
            field
            for field, value in required_fields.items()
            if not value
        ]

        if missing_fields:
            errors.append(
                f"Row {row_number}: Missing required "
                f"field(s): {', '.join(missing_fields)}."
            )
            continue

        # --------------------------------------------------
        # Semester number
        # --------------------------------------------------

        try:
            semester_number = int(
                semester_number
            )

            if semester_number <= 0:
                raise ValueError

        except (TypeError, ValueError):
            errors.append(
                f"Row {row_number}: Invalid semester "
                f"number '{row['semester_number']}'."
            )
            continue

        # --------------------------------------------------
        # Teacher
        # --------------------------------------------------

        teacher = (
            Teacher.objects
            .select_related("user")
            .filter(
                employee_id=employee_id
            )
            .first()
        )

        if teacher is None:
            errors.append(
                f"Row {row_number}: Teacher with employee "
                f"ID '{employee_id}' does not exist."
            )
            continue

        # --------------------------------------------------
        # Institution
        # --------------------------------------------------

        institution = (
            Institution.objects
            .filter(
                short_name__iexact=(
                    institution_short_name
                )
            )
            .first()
        )

        if institution is None:
            errors.append(
                f"Row {row_number}: Institution "
                f"'{institution_short_name}' does not exist."
            )
            continue

        # --------------------------------------------------
        # Department
        # --------------------------------------------------

        department = (
            Department.objects
            .filter(
                institution=institution,
                code__iexact=department_code,
            )
            .first()
        )

        if department is None:
            errors.append(
                f"Row {row_number}: Department "
                f"'{department_code}' does not exist "
                f"in institution "
                f"'{institution.short_name}'."
            )
            continue

        # --------------------------------------------------
        # Course
        # --------------------------------------------------

        course = (
            Course.objects
            .filter(
                department=department,
                code__iexact=course_code,
            )
            .first()
        )

        if course is None:
            errors.append(
                f"Row {row_number}: Course "
                f"'{course_code}' does not exist "
                f"in department "
                f"'{department.code}'."
            )
            continue

        # --------------------------------------------------
        # Semester
        # --------------------------------------------------

        semester = (
            Semester.objects
            .filter(
                course=course,
                semester_number=semester_number,
            )
            .first()
        )

        if semester is None:
            errors.append(
                f"Row {row_number}: Semester "
                f"{semester_number} does not exist "
                f"for course '{course.code}'."
            )
            continue

        # --------------------------------------------------
        # Subject
        # --------------------------------------------------

        subject = (
            Subject.objects
            .filter(
                semester=semester,
                code__iexact=subject_code,
            )
            .first()
        )

        if subject is None:
            errors.append(
                f"Row {row_number}: Subject "
                f"'{subject_code}' does not exist "
                f"for semester {semester_number}."
            )
            continue

        # --------------------------------------------------
        # Duplicate inside CSV
        # --------------------------------------------------

        assignment_key = (
            teacher.pk,
            course.pk,
            semester.pk,
            subject.pk,
        )

        if assignment_key in seen_assignments:
            errors.append(
                f"Row {row_number}: Duplicate teaching "
                f"assignment in the CSV."
            )
            continue

        seen_assignments.add(
            assignment_key
        )

        # --------------------------------------------------
        # Existing assignment
        # --------------------------------------------------

        if TeachingAssignment.objects.filter(
            teacher=teacher,
            course=course,
            semester=semester,
            subject=subject,
        ).exists():

            errors.append(
                f"Row {row_number}: This teaching "
                f"assignment already exists."
            )
            continue

        validated_rows.append(
            {
                "row_number": row_number,
                "employee_id": teacher.employee_id,
                "teacher": teacher,
                "institution": institution,
                "department": department,
                "course": course,
                "semester": semester,
                "subject": subject,
            }
        )

    if errors:
        raise TeacherAssignmentCSVImportError(
            "\n".join(errors)
        )

    return validated_rows


@transaction.atomic
def import_assignment_rows(rows):
    """
    Create all assignments atomically.
    """

    results = []

    for row in rows:

        assignment = (
            TeacherService.create_teaching_assignment(
                teacher=row["teacher"],
                course=row["course"],
                semester=row["semester"],
                subject=row["subject"],
            )
        )

        results.append(
            {
                "employee_id": row["employee_id"],
                "course": row["course"].name,
                "semester": row["semester"].name,
                "subject": row["subject"].name,
                "assignment_id": assignment.pk,
            }
        )

    return results


def generate_assignment_csv_template():
    """
    Generate the CSV template.
    """

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        ASSIGNMENT_CSV_COLUMNS
    )

    return output.getvalue()