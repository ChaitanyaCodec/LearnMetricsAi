"""
Business logic for the Teachers module.

Views should use these services for write operations.
"""


from __future__ import annotations

from django.db import transaction

from apps.accounts.models import User

from .models import Teacher, TeachingAssignment


class TeacherServiceError(Exception):
    """
    Base exception for Teacher service errors.
    """

    pass


class TeacherService:

    # ======================================================
    # Teacher
    # ======================================================

    @staticmethod
    @transaction.atomic
    def create_teacher_with_user(
        *,
        email,
        password,
        first_name,
        last_name,
        phone_number="",
        employee_id,
        joining_date=None,
    ):
        """
        Create a TEACHER User and Teacher profile atomically.
        """

        email = email.strip().lower()
        employee_id = employee_id.strip()

        if User.objects.filter(
            email=email
        ).exists():
            raise TeacherServiceError(
                f"A user with email '{email}' already exists."
            )

        if Teacher.objects.filter(
            employee_id=employee_id
        ).exists():
            raise TeacherServiceError(
                f"Employee ID '{employee_id}' already exists."
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=User.Roles.TEACHER,
        )

        return Teacher.objects.create(
            user=user,
            employee_id=employee_id,
            joining_date=joining_date,
        )

    @staticmethod
    @transaction.atomic
    def update_teacher(
        teacher,
        *,
        email,
        first_name,
        last_name,
        phone_number="",
        employee_id,
        joining_date=None,
    ):
        """
        Update Teacher and its associated User.
        """

        email = email.strip().lower()
        employee_id = employee_id.strip()

        if User.objects.filter(
            email=email
        ).exclude(
            pk=teacher.user.pk
        ).exists():
            raise TeacherServiceError(
                f"A user with email '{email}' already exists."
            )

        if Teacher.objects.filter(
            employee_id=employee_id
        ).exclude(
            pk=teacher.pk
        ).exists():
            raise TeacherServiceError(
                f"Employee ID '{employee_id}' already exists."
            )

        user = teacher.user

        # The Teacher profile must always belong
        # to a TEACHER role.
        user.role = User.Roles.TEACHER
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

        teacher.employee_id = employee_id
        teacher.joining_date = joining_date

        teacher.save(
            update_fields=[
                "employee_id",
                "joining_date",
                "updated_at",
            ]
        )

        return teacher

    # ======================================================
    # Teaching Assignment
    # ======================================================

    @staticmethod
    def validate_assignment_relationships(
        *,
        course,
        semester,
        subject,
    ):
        """
        Validate the academic hierarchy:

        Course
          ↓
        Semester
          ↓
        Subject
        """

        if semester.course_id != course.pk:
            raise TeacherServiceError(
                "The selected semester does not belong "
                "to the selected course."
            )

        if subject.semester_id != semester.pk:
            raise TeacherServiceError(
                "The selected subject does not belong "
                "to the selected semester."
            )

        if subject.semester.course_id != course.pk:
            raise TeacherServiceError(
                "The selected subject does not belong "
                "to the selected course."
            )

    @staticmethod
    @transaction.atomic
    def create_teaching_assignment(
        *,
        teacher,
        course,
        semester,
        subject,
    ):
        """
        Create a teaching assignment after validating
        the academic hierarchy and duplicate assignment.
        """

        TeacherService.validate_assignment_relationships(
            course=course,
            semester=semester,
            subject=subject,
        )

        if TeachingAssignment.objects.filter(
            teacher=teacher,
            course=course,
            semester=semester,
            subject=subject,
        ).exists():
            raise TeacherServiceError(
                "This teaching assignment already exists."
            )

        return TeachingAssignment.objects.create(
            teacher=teacher,
            course=course,
            semester=semester,
            subject=subject,
        )

    @staticmethod
    @transaction.atomic
    def update_teaching_assignment(
        assignment,
        *,
        teacher,
        course,
        semester,
        subject,
    ):
        """
        Update a teaching assignment after validating
        the academic hierarchy and duplicate assignment.
        """

        TeacherService.validate_assignment_relationships(
            course=course,
            semester=semester,
            subject=subject,
        )

        if TeachingAssignment.objects.filter(
            teacher=teacher,
            course=course,
            semester=semester,
            subject=subject,
        ).exclude(
            pk=assignment.pk
        ).exists():
            raise TeacherServiceError(
                "This teaching assignment already exists."
            )

        assignment.teacher = teacher
        assignment.course = course
        assignment.semester = semester
        assignment.subject = subject

        assignment.save()

        return assignment


# ==========================================================
# CRUD-compatible service functions
# ==========================================================

def create_teacher(
    *,
    email,
    password,
    password_confirm,
    first_name,
    last_name,
    phone_number,
    employee_id,
    joining_date,
):
    """
    Adapter used by BaseCreateView.

    password_confirm is validated by the form.
    """

    return TeacherService.create_teacher_with_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        employee_id=employee_id,
        joining_date=joining_date,
    )


def update_teacher(
    teacher,
    *,
    email,
    first_name,
    last_name,
    phone_number,
    employee_id,
    joining_date,
):
    """
    Adapter used by BaseUpdateView.
    """

    return TeacherService.update_teacher(
        teacher,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        employee_id=employee_id,
        joining_date=joining_date,
    )


def create_teaching_assignment(
    *,
    teacher,
    course,
    semester,
    subject,
):
    """
    Adapter used by BaseCreateView.
    """

    return TeacherService.create_teaching_assignment(
        teacher=teacher,
        course=course,
        semester=semester,
        subject=subject,
    )


def update_teaching_assignment(
    assignment,
    *,
    teacher,
    course,
    semester,
    subject,
):
    """
    Adapter used by BaseUpdateView.
    """

    return TeacherService.update_teaching_assignment(
        assignment,
        teacher=teacher,
        course=course,
        semester=semester,
        subject=subject,
    )