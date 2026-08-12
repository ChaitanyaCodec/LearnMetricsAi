"""
Student services.

Write operations and business rules for the Students module.

Views must use these services instead of performing database
business logic directly.
"""

from __future__ import annotations

from django.db import transaction

from apps.accounts.models import User

from .models import Student, StudentEnrollment


class StudentServiceError(Exception):
    """
    Base exception for Student service errors.
    """

    pass


class StudentService:

    @staticmethod
    @transaction.atomic
    def create_student_with_user(
        *,
        email,
        password,
        first_name,
        last_name,
        phone_number="",
        student_id,
        admission_date=None,
    ):
        """
        Create a STUDENT User and Student profile atomically.
        """

        email = email.strip().lower()
        student_id = student_id.strip()

        if User.objects.filter(
            email=email
        ).exists():
            raise StudentServiceError(
                f"A user with email '{email}' already exists."
            )

        if Student.objects.filter(
            student_id=student_id
        ).exists():
            raise StudentServiceError(
                f"Student ID '{student_id}' already exists."
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=User.Roles.STUDENT,
        )

        return Student.objects.create(
            user=user,
            student_id=student_id,
            admission_date=admission_date,
        )

    @staticmethod
    @transaction.atomic
    def update_student(
        student,
        *,
        email,
        first_name,
        last_name,
        phone_number="",
        student_id,
        admission_date=None,
    ):
        """
        Update Student and its associated User.
        """

        student_id = student_id.strip()
        email = email.strip().lower()

        if User.objects.filter(
            email=email
        ).exclude(
            pk=student.user.pk
        ).exists():
            raise StudentServiceError(
                f"A user with email '{email}' already exists."
            )

        if Student.objects.filter(
            student_id=student_id
        ).exclude(
            pk=student.pk
        ).exists():
            raise StudentServiceError(
                f"Student ID '{student_id}' already exists."
            )

        user = student.user

        # Never allow the form to change the role.
        user.role = User.Roles.STUDENT
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number

        user.save(
            update_fields=[
                "role",
                "email",
                "first_name",
                "last_name",
                "phone_number",
                "updated_at",
            ]
        )

        student.student_id = student_id
        student.admission_date = admission_date

        student.save(
            update_fields=[
                "student_id",
                "admission_date",
                "updated_at",
            ]
        )

        return student

    @staticmethod
    @transaction.atomic
    def create_enrollment(
        *,
        student,
        course,
        semester,
        academic_year,
        roll_number,
        enrollment_date,
        status=StudentEnrollment.Status.ACTIVE,
    ):
        """
        Create a StudentEnrollment after validating
        the academic relationship.
        """

        if semester.course_id != course.pk:
            raise StudentServiceError(
                "The selected semester does not belong "
                "to the selected course."
            )

        if StudentEnrollment.objects.filter(
            student=student,
            academic_year=academic_year,
        ).exists():
            raise StudentServiceError(
                "This student is already enrolled "
                f"for academic year '{academic_year}'."
            )

        if StudentEnrollment.objects.filter(
            course=course,
            academic_year=academic_year,
            roll_number=roll_number,
        ).exists():
            raise StudentServiceError(
                f"Roll number '{roll_number}' already exists "
                "for this course and academic year."
            )

        return StudentEnrollment.objects.create(
            student=student,
            course=course,
            semester=semester,
            academic_year=academic_year,
            roll_number=roll_number,
            enrollment_date=enrollment_date,
            status=status,
        )

    @staticmethod
    @transaction.atomic
    def update_enrollment(
        enrollment,
        *,
        student,
        course,
        semester,
        academic_year,
        roll_number,
        enrollment_date,
        status,
    ):
        """
        Update an existing StudentEnrollment.
        """

        if semester.course_id != course.pk:
            raise StudentServiceError(
                "The selected semester does not belong "
                "to the selected course."
            )

        if StudentEnrollment.objects.filter(
            student=student,
            academic_year=academic_year,
        ).exclude(
            pk=enrollment.pk
        ).exists():
            raise StudentServiceError(
                "This student is already enrolled "
                f"for academic year '{academic_year}'."
            )

        if StudentEnrollment.objects.filter(
            course=course,
            academic_year=academic_year,
            roll_number=roll_number,
        ).exclude(
            pk=enrollment.pk
        ).exists():
            raise StudentServiceError(
                f"Roll number '{roll_number}' already exists "
                "for this course and academic year."
            )

        enrollment.student = student
        enrollment.course = course
        enrollment.semester = semester
        enrollment.academic_year = academic_year
        enrollment.roll_number = roll_number
        enrollment.enrollment_date = enrollment_date
        enrollment.status = status

        enrollment.save()

        return enrollment


# ==========================================================
# CRUD-compatible service functions
# ==========================================================

def create_student(
    *,
    email,
    password,
    password_confirm,
    first_name,
    last_name,
    phone_number,
    student_id,
    admission_date,
):
    """
    Adapter for BaseCreateView.

    password_confirm is already validated by the form.
    """

    return StudentService.create_student_with_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        student_id=student_id,
        admission_date=admission_date,
    )


def update_student(
    student,
    *,
    email,
    first_name,
    last_name,
    phone_number,
    student_id,
    admission_date,
):
    """
    Adapter for BaseUpdateView.
    """

    return StudentService.update_student(
        student,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        student_id=student_id,
        admission_date=admission_date,
    )


def create_enrollment(
    *,
    student,
    course,
    semester,
    academic_year,
    roll_number,
    enrollment_date,
    status,
):
    """
    Adapter for BaseCreateView.
    """

    return StudentService.create_enrollment(
        student=student,
        course=course,
        semester=semester,
        academic_year=academic_year,
        roll_number=roll_number,
        enrollment_date=enrollment_date,
        status=status,
    )


def update_enrollment(
    enrollment,
    *,
    student,
    course,
    semester,
    academic_year,
    roll_number,
    enrollment_date,
    status,
):
    """
    Adapter for BaseUpdateView.
    """

    return StudentService.update_enrollment(
        enrollment,
        student=student,
        course=course,
        semester=semester,
        academic_year=academic_year,
        roll_number=roll_number,
        enrollment_date=enrollment_date,
        status=status,
    )