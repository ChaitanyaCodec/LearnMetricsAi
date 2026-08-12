from django.shortcuts import render
from django.http import JsonResponse
from django.views import View

from apps.academics.models import Semester, Subject

# Create your views here.
"""
Views for the Teachers module.
"""

from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.accounts.mixins import AdminRequiredMixin

from apps.core.views.crud import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
)

from .forms import (
    TeacherCreateForm,
    TeacherForm,
    TeachingAssignmentForm,
)

from .models import (
    Teacher,
    TeachingAssignment,
)

from .selectors import (
    get_teachers,
    get_teaching_assignments,
)

from .services import (
    create_teacher,
    update_teacher,
    create_teaching_assignment,
    update_teaching_assignment,
)


class TeacherManagementDashboardView(
    AdminRequiredMixin,
    TemplateView,
):
    """
    Administrator Teacher Management Dashboard.
    """

    template_name = (
        "teachers/dashboard.html"
    )


# ==========================================================
# Teacher Management
# ==========================================================

class TeacherListView(
    AdminRequiredMixin,
    BaseListView,
):

    model = Teacher

    selector = get_teachers

    template_name = (
        "teachers/teacher/list.html"
    )

    context_object_name = "teachers"

    page_title = "Teacher Management"

    page_subtitle = "Manage teachers"

    filter_parameters = ()

    default_ordering = (
        "employee_id",
    )

    allowed_ordering = (
        "employee_id",
        "-employee_id",
        "user__first_name",
        "-user__first_name",
        "user__last_name",
        "-user__last_name",
        "joining_date",
        "-joining_date",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "employee_id": "Employee ID (A-Z)",
        "-employee_id": "Employee ID (Z-A)",
        "user__first_name": "First Name (A-Z)",
        "-user__first_name": "First Name (Z-A)",
        "user__last_name": "Last Name (A-Z)",
        "-user__last_name": "Last Name (Z-A)",
        "joining_date": "Joining Date (Oldest)",
        "-joining_date": "Joining Date (Newest)",
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class TeacherCreateView(
    AdminRequiredMixin,
    BaseCreateView,
):

    form_class = TeacherCreateForm

    template_name = (
        "teachers/teacher/form.html"
    )

    success_url = reverse_lazy(
        "teachers:teacher-list"
    )

    service = create_teacher

    success_message = (
        "Teacher created successfully."
    )


class TeacherUpdateView(
    AdminRequiredMixin,
    BaseUpdateView,
):

    model = Teacher

    form_class = TeacherForm

    template_name = (
        "teachers/teacher/form.html"
    )

    success_url = reverse_lazy(
        "teachers:teacher-list"
    )

    service = update_teacher

    success_message = (
        "Teacher updated successfully."
    )


# ==========================================================
# Teaching Assignment Management
# ==========================================================

class TeachingAssignmentListView(
    AdminRequiredMixin,
    BaseListView,
):

    model = TeachingAssignment

    selector = get_teaching_assignments

    template_name = (
        "teachers/assignment/list.html"
    )

    context_object_name = "assignments"

    page_title = "Teaching Assignments"

    page_subtitle = (
        "Manage teacher subject assignments"
    )

    filter_parameters = (
        "course",
        "semester",
        "subject",
    )

    default_ordering = (
        "teacher__employee_id",
    )

    allowed_ordering = (
        "teacher__employee_id",
        "-teacher__employee_id",
        "course__name",
        "-course__name",
        "semester__semester_number",
        "-semester__semester_number",
        "subject__name",
        "-subject__name",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "teacher__employee_id": "Employee ID",
        "-teacher__employee_id": (
            "Employee ID (Descending)"
        ),
        "course__name": "Course (A-Z)",
        "-course__name": "Course (Z-A)",
        "semester__semester_number": "Semester",
        "-semester__semester_number": (
            "Semester (Descending)"
        ),
        "subject__name": "Subject (A-Z)",
        "-subject__name": "Subject (Z-A)",
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class TeachingAssignmentCreateView(
    AdminRequiredMixin,
    BaseCreateView,
):

    form_class = TeachingAssignmentForm

    template_name = (
        "teachers/assignment/form.html"
    )

    success_url = reverse_lazy(
        "teachers:assignment-list"
    )

    service = create_teaching_assignment

    success_message = (
        "Teaching assignment created successfully."
    )


class TeachingAssignmentUpdateView(
    AdminRequiredMixin,
    BaseUpdateView,
):

    model = TeachingAssignment

    form_class = TeachingAssignmentForm

    template_name = (
        "teachers/assignment/form.html"
    )

    success_url = reverse_lazy(
        "teachers:assignment-list"
    )

    service = update_teaching_assignment

    success_message = (
        "Teaching assignment updated successfully."
    )

class SemesterOptionsView(
    AdminRequiredMixin,
    View,
):
    """
    Return semesters belonging to a selected course.
    """

    def get(self, request, *args, **kwargs):

        course_id = request.GET.get("course_id")

        if not course_id:
            return JsonResponse(
                {"results": []}
            )

        semesters = (
            Semester.objects
            .filter(course_id=course_id)
            .order_by("semester_number")
        )

        return JsonResponse(
            {
                "results": [
                    {
                        "id": semester.pk,
                        "name": semester.name,
                        "semester_number": (
                            semester.semester_number
                        ),
                    }
                    for semester in semesters
                ]
            }
        )


class SubjectOptionsView(
    AdminRequiredMixin,
    View,
):
    """
    Return subjects belonging to a selected semester.
    """

    def get(self, request, *args, **kwargs):

        semester_id = request.GET.get(
            "semester_id"
        )

        if not semester_id:
            return JsonResponse(
                {"results": []}
            )

        subjects = (
            Subject.objects
            .filter(
                semester_id=semester_id
            )
            .order_by("name")
        )

        return JsonResponse(
            {
                "results": [
                    {
                        "id": subject.pk,
                        "code": subject.code,
                        "name": subject.name,
                    }
                    for subject in subjects
                ]
            }
        )