"""
Views for the Academics application.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView

from apps.core.views.crud import (
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
)

from .forms import (
    InstitutionForm,
    DepartmentForm,
    CourseForm,
    SemesterForm,
    SubjectForm,
)

from .models import (
    Institution,
    Department,
    Course,
    Semester,
    Subject,
)

from .selectors import (
    get_institutions,
    get_departments,
    get_courses,
    get_semesters,
    get_subjects,
)

from .services import (
    create_institution,
    update_institution,
    delete_institution,

    create_department,
    update_department,
    delete_department,

    create_course,
    update_course,
    delete_course,

    create_semester,
    update_semester,
    delete_semester,

    create_subject,
    update_subject,
    delete_subject,
)


# ==========================================================
# Dashboard
# ==========================================================

class AcademicsDashboardView(TemplateView):
    """
    Academic Management Dashboard.
    """

    template_name = "academics/dashboard.html"


# ==========================================================
# Institution Views
# ==========================================================

class InstitutionListView(ListView):

    model = Institution

    template_name = "academics/institution/list.html"

    context_object_name = "institutions"

    def get_queryset(self):
        return get_institutions()


class InstitutionCreateView(BaseCreateView):

    form_class = InstitutionForm

    template_name = "academics/institution/form.html"

    success_url = reverse_lazy(
        "academics:institution-list"
    )

    service = create_institution

    success_message = (
        "Institution created successfully."
    )


class InstitutionUpdateView(BaseUpdateView):

    model = Institution

    form_class = InstitutionForm

    template_name = "academics/institution/form.html"

    success_url = reverse_lazy(
        "academics:institution-list"
    )

    service = update_institution

    success_message = (
        "Institution updated successfully."
    )


class InstitutionDeleteView(BaseDeleteView):

    model = Institution

    template_name = (
        "academics/institution/confirm_delete.html"
    )

    success_url = reverse_lazy(
        "academics:institution-list"
    )

    service = delete_institution

    success_message = (
        "Institution deleted successfully."
    )


# ==========================================================
# Department Views
# ==========================================================

class DepartmentListView(ListView):

    model = Department

    template_name = "academics/department/list.html"

    context_object_name = "departments"

    def get_queryset(self):
        return get_departments()


class DepartmentCreateView(BaseCreateView):

    form_class = DepartmentForm

    template_name = "academics/department/form.html"

    success_url = reverse_lazy(
        "academics:department-list"
    )

    service = create_department

    success_message = (
        "Department created successfully."
    )


class DepartmentUpdateView(BaseUpdateView):

    model = Department

    form_class = DepartmentForm

    template_name = "academics/department/form.html"

    success_url = reverse_lazy(
        "academics:department-list"
    )

    service = update_department

    success_message = (
        "Department updated successfully."
    )


class DepartmentDeleteView(BaseDeleteView):

    model = Department

    template_name = (
        "academics/department/confirm_delete.html"
    )

    success_url = reverse_lazy(
        "academics:department-list"
    )

    service = delete_department

    success_message = (
        "Department deleted successfully."
    )


# ==========================================================
# Course Views
# ==========================================================

class CourseListView(ListView):

    model = Course

    template_name = "academics/course/list.html"

    context_object_name = "courses"

    def get_queryset(self):
        return get_courses()


class CourseCreateView(BaseCreateView):

    form_class = CourseForm

    template_name = "academics/course/form.html"

    success_url = reverse_lazy(
        "academics:course-list"
    )

    service = create_course

    success_message = (
        "Course created successfully."
    )


class CourseUpdateView(BaseUpdateView):

    model = Course

    form_class = CourseForm

    template_name = "academics/course/form.html"

    success_url = reverse_lazy(
        "academics:course-list"
    )

    service = update_course

    success_message = (
        "Course updated successfully."
    )


class CourseDeleteView(BaseDeleteView):

    model = Course

    template_name = (
        "academics/course/confirm_delete.html"
    )

    success_url = reverse_lazy(
        "academics:course-list"
    )

    service = delete_course

    success_message = (
        "Course deleted successfully."
    )

    # ==========================================================
# Semester Views
# ==========================================================

class SemesterListView(ListView):
    """
    Display all semesters.
    """

    model = Semester

    template_name = "academics/semester/list.html"

    context_object_name = "semesters"

    def get_queryset(self):
        return get_semesters()


class SemesterCreateView(BaseCreateView):
    """
    Create a new semester.
    """

    form_class = SemesterForm

    template_name = "academics/semester/form.html"

    success_url = reverse_lazy(
        "academics:semester-list"
    )

    service = create_semester

    success_message = (
        "Semester created successfully."
    )


class SemesterUpdateView(BaseUpdateView):
    """
    Update an existing semester.
    """

    model = Semester

    form_class = SemesterForm

    template_name = "academics/semester/form.html"

    success_url = reverse_lazy(
        "academics:semester-list"
    )

    service = update_semester

    success_message = (
        "Semester updated successfully."
    )


class SemesterDeleteView(BaseDeleteView):
    """
    Delete a semester.
    """

    model = Semester

    template_name = (
        "academics/semester/confirm_delete.html"
    )

    success_url = reverse_lazy(
        "academics:semester-list"
    )

    service = delete_semester

    success_message = (
        "Semester deleted successfully."
    )


# ==========================================================
# Subject Views
# ==========================================================

class SubjectListView(ListView):
    """
    Display all subjects.
    """

    model = Subject

    template_name = "academics/subject/list.html"

    context_object_name = "subjects"

    def get_queryset(self):
        return get_subjects()


class SubjectCreateView(BaseCreateView):
    """
    Create a new subject.
    """

    form_class = SubjectForm

    template_name = "academics/subject/form.html"

    success_url = reverse_lazy(
        "academics:subject-list"
    )

    service = create_subject

    success_message = (
        "Subject created successfully."
    )


class SubjectUpdateView(BaseUpdateView):
    """
    Update an existing subject.
    """

    model = Subject

    form_class = SubjectForm

    template_name = "academics/subject/form.html"

    success_url = reverse_lazy(
        "academics:subject-list"
    )

    service = update_subject

    success_message = (
        "Subject updated successfully."
    )


class SubjectDeleteView(BaseDeleteView):
    """
    Delete a subject.
    """

    model = Subject

    template_name = (
        "academics/subject/confirm_delete.html"
    )

    success_url = reverse_lazy(
        "academics:subject-list"
    )

    service = delete_subject

    success_message = (
        "Subject deleted successfully."
    )