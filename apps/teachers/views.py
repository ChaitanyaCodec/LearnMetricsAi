from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse,HttpResponse
from django.views import View


from apps.academics.models import Semester, Subject
from apps.accounts.models import User
from apps.accounts.mixins import (
    AdminRequiredMixin,
    TeacherRequiredMixin,
)

# Create your views here.
"""
Views for the Teachers module.
"""

from django.urls import reverse_lazy
from django.views.generic import TemplateView


from apps.core.views.crud import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
)
from django.contrib import messages
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
    get_teacher,
    get_teaching_assignments,
    get_teacher_by_user,
    get_teacher_assignments,    
)

from .services import (
    create_teacher,
    update_teacher,
    create_teaching_assignment,
    update_teaching_assignment,
)


from .csv.service import (
    TeacherCSVImportError,
    TeacherCSVImportService,
    )
from .csv.assignment import (
    TeacherAssignmentCSVImportError,
    read_assignment_csv,
    validate_assignment_rows,
    import_assignment_rows,
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

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        total_teachers = Teacher.objects.count()

        active_teachers = Teacher.objects.filter(
            user__is_active=True,
            user__role=User.Roles.TEACHER,
        ).count()

        total_assignments = (
            TeachingAssignment.objects.count()
        )

        total_courses = (
            TeachingAssignment.objects
            .values("course_id")
            .distinct()
            .count()
        )

        recent_assignments = (
            TeachingAssignment.objects
            .select_related(
                "teacher",
                "teacher__user",
                "course",
                "course__department",
                "course__department__institution",
                "semester",
                "subject",
            )
            .order_by("-created_at")[:10]
        )

        context.update(
            {
                "total_teachers": total_teachers,
                "active_teachers": active_teachers,
                "total_assignments": total_assignments,
                "total_courses": total_courses,
                "recent_assignments": recent_assignments,
            }
        )

        return context

# ==========================================================
# Teacher Management
# =========================================================

class TeacherDashboardView(
    TeacherRequiredMixin,
    TemplateView,
):
    """
    Dashboard for the authenticated teacher.

    Only assignments belonging to the logged-in
    teacher are exposed.
    """

    template_name = (
        "teachers/teacher/dashboard.html"
    )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        teacher = get_teacher_by_user(
            self.request.user.pk
        )

        if teacher is None:
            context["teacher"] = None
            context["assignments"] = []
            return context

        assignments = get_teacher_assignments(
            teacher.pk
        )

        context["teacher"] = teacher
        context["assignments"] = assignments

        return context

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
class TeacherDetailView(
    AdminRequiredMixin,
    TemplateView,
):
    """
    Display a Teacher profile and their
    teaching assignments.
    """

    template_name = (
        "teachers/teacher/detail.html"
    )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        teacher = get_teacher(
            self.kwargs["pk"]
        )

        if teacher is None:
            from django.http import Http404
            raise Http404("Teacher not found.")

        context["teacher"] = teacher

        context["assignments"] = (
            get_teacher_assignments(
                teacher.pk
            )
        )

        return context

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

class TeachingAssignmentImportView(
    AdminRequiredMixin,
    View,
):
    """
    Bulk import teaching assignments from CSV.
    """

    template_name = (
        "teachers/assignment/import.html"
    )

    def get(self, request, *args, **kwargs):

        return render(
            request,
            self.template_name,
        )

    def post(self, request, *args, **kwargs):

        csv_file = request.FILES.get("csv_file")

        if not csv_file:

            return render(
                request,
                self.template_name,
                {
                    "import_errors": [
                        "Please select a CSV file."
                    ]
                },
            )

        try:

            rows = read_assignment_csv(
                csv_file
            )

            validated_rows = (
                validate_assignment_rows(rows)
            )

            import_results = (
                import_assignment_rows(
                    validated_rows
                )
            )

            messages.success(
                request,
                (
                    f"{len(import_results)} teaching "
                    "assignment(s) imported successfully."
                ),
            )

            return render(
                request,
                self.template_name,
                {
                    "import_results": import_results,
                },
            )

        except TeacherAssignmentCSVImportError as exc:

            return render(
                request,
                self.template_name,
                {
                    "import_errors": str(exc).splitlines(),
                },
            )
class TeachingAssignmentImportTemplateView(
    AdminRequiredMixin,
    View,
):
    """
    Download the CSV template for bulk
    teaching assignment import.
    """

    def get(self, request, *args, **kwargs):

        from .csv.assignment import (
            generate_assignment_csv_template,
        )

        response = HttpResponse(
            generate_assignment_csv_template(),
            content_type="text/csv",
        )

        response[
            "Content-Disposition"
        ] = (
            'attachment; '
            'filename="teaching_assignment_template.csv"'
        )

        return response
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

class TeacherBulkImportView(
    AdminRequiredMixin,
    View,
):
    """
    Admin-only bulk Teacher CSV import.
    """

    template_name = (
        "teachers/teacher/import.html"
    )

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
        )

    def post(self, request, *args, **kwargs):

        uploaded_file = request.FILES.get(
            "csv_file"
        )

        if not uploaded_file:
            return render(
                request,
                self.template_name,
                {
                    "import_errors": [
                        "Please select a CSV file."
                    ]
                },
            )

        if not uploaded_file.name.lower().endswith(
            ".csv"
        ):
            return render(
                request,
                self.template_name,
                {
                    "import_errors": [
                        "Only CSV files are supported."
                    ]
                },
            )

        try:

            results = (
                TeacherCSVImportService.import_csv(
                    uploaded_file
                )
            )

        except TeacherCSVImportError as exc:

            return render(
                request,
                self.template_name,
                {
                    "import_errors": exc.args[0],
                },
            )

        messages.success(
            request,
            (
                f"{len(results)} teacher(s) "
                "imported successfully."
            ),
        )

        return render(
            request,
            self.template_name,
            {
                "import_results": results,
            },
        )
    
class TeacherCSVTemplateView(
    AdminRequiredMixin,
    View,
):
    """
    Download the standard Teacher CSV import template.
    """

    def get(self, request, *args, **kwargs):

        csv_content = (
            "email,first_name,last_name,phone_number,"
            "employee_id,joining_date\n"
            "teacher@example.com,Rahul,Patil,9876543210,"
            "TCH001,2026-06-01\n"
        )

        response = HttpResponse(
            csv_content,
            content_type="text/csv",
        )

        response["Content-Disposition"] = (
            'attachment; filename="teacher_import_template.csv"'
        )

        return response