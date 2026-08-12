"""
Views for the Students application.
"""
from apps.accounts.mixins import AdminRequiredMixin

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.core.views.crud import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
)

from .forms import (
    StudentCreateForm,
    StudentForm,
    StudentEnrollmentForm,
)

from .models import (
    Student,
    StudentEnrollment,
)

from .selectors import (
    get_students,
    get_student_enrollments,
)

from .services import (
    create_student,
    update_student,
    create_enrollment,
    update_enrollment,
)


# ==========================================================
# Student Dashboard
# ==========================================================

class StudentManagementDashboardView(
    AdminRequiredMixin,
    TemplateView
):
    """
    Administrator Student Management Dashboard.
    """

    template_name = (
        "students/dashboard.html"
    )


# ==========================================================
# Student Views
# ==========================================================

class StudentListView(BaseListView, AdminRequiredMixin):

    model = Student

    selector = get_students

    template_name = (
        "students/student/list.html"
    )

    context_object_name = "students"

    page_title = "Student Management"

    page_subtitle = "Manage students"

    filter_parameters = ()

    default_ordering = (
        "student_id",
    )

    allowed_ordering = (
        "student_id",
        "-student_id",
        "user__first_name",
        "-user__first_name",
        "user__last_name",
        "-user__last_name",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "student_id": "Student ID (A-Z)",
        "-student_id": "Student ID (Z-A)",
        "user__first_name": "First Name (A-Z)",
        "-user__first_name": "First Name (Z-A)",
        "user__last_name": "Last Name (A-Z)",
        "-user__last_name": "Last Name (Z-A)",
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class StudentCreateView(BaseCreateView, AdminRequiredMixin):

    form_class = StudentCreateForm

    template_name = (
        "students/student/form.html"
    )

    success_url = reverse_lazy(
        "students:student-list"
    )

    service = create_student

    success_message = (
        "Student created successfully."
    )


class StudentUpdateView(BaseUpdateView, AdminRequiredMixin):

    model = Student

    form_class = StudentForm

    template_name = (
        "students/student/form.html"
    )

    success_url = reverse_lazy(
        "students:student-list"
    )

    service = update_student

    success_message = (
        "Student updated successfully."
    )


# ==========================================================
# Enrollment Views
# ==========================================================

class StudentEnrollmentListView(
    BaseListView,
    AdminRequiredMixin
):

    model = StudentEnrollment

    selector = get_student_enrollments

    template_name = (
        "students/enrollment/list.html"
    )

    context_object_name = "enrollments"

    page_title = "Student Enrollments"

    page_subtitle = (
        "Manage student academic enrollments"
    )

    filter_parameters = (
        "course",
        "semester",
        "academic_year",
        "status",
    )

    default_ordering = (
        "-academic_year",
        "roll_number",
    )

    allowed_ordering = (
        "student__student_id",
        "-student__student_id",
        "course__name",
        "-course__name",
        "semester__semester_number",
        "-semester__semester_number",
        "academic_year",
        "-academic_year",
        "roll_number",
        "-roll_number",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "student__student_id": "Student ID",
        "-student__student_id": "Student ID (Descending)",
        "course__name": "Course (A-Z)",
        "-course__name": "Course (Z-A)",
        "semester__semester_number": "Semester",
        "-semester__semester_number": (
            "Semester (Descending)"
        ),
        "academic_year": "Academic Year",
        "-academic_year": (
            "Academic Year (Descending)"
        ),
        "roll_number": "Roll Number",
        "-roll_number": (
            "Roll Number (Descending)"
        ),
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class StudentEnrollmentCreateView(
    BaseCreateView, AdminRequiredMixin
):

    form_class = StudentEnrollmentForm

    template_name = (
        "students/enrollment/form.html"
    )

    success_url = reverse_lazy(
        "students:enrollment-list"
    )

    service = create_enrollment

    success_message = (
        "Student enrollment created successfully."
    )


class StudentEnrollmentUpdateView(
    BaseUpdateView, AdminRequiredMixin
):

    model = StudentEnrollment

    form_class = StudentEnrollmentForm

    template_name = (
        "students/enrollment/form.html"
    )

    success_url = reverse_lazy(
        "students:enrollment-list"
    )

    service = update_enrollment

    success_message = (
        "Student enrollment updated successfully."
    )