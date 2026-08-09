"""
Views for the Academics application.
"""
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView

from apps.core.views.crud import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
)

from .csv.service import (
    CSVImportError,
    import_rows,
)

from .csv.institution import (
    read_institution_csv,
    validate_institution_rows,
    create_institution_from_csv_row,
)

from .csv.department import (
    read_department_csv,
    validate_department_rows,
    create_department_from_csv_row,
)

from .csv.course import (
    read_course_csv,
    validate_course_rows,
    create_course_from_csv_row,
)
from .csv.semester import (
    read_semester_csv,
    validate_semester_rows,
    create_semester_from_csv_row,
)
from .csv.subject import (
    read_subject_csv,
    validate_subject_rows,
    create_subject_from_csv_row,
)

from .forms import (
    InstitutionForm,
    DepartmentForm,
    CourseForm,
    SemesterForm,
    SubjectForm,
    InstitutionCSVImportForm,
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

class InstitutionListView(BaseListView):

    model = Institution

    selector = get_institutions

    template_name = (
        "academics/institution/list.html"
    )

    context_object_name = "institutions"

    page_title = "Institution Management"

    page_subtitle = "Manage institutions"

    filter_parameters = (
        "is_active",
    )

    default_ordering = (
        "name",
    )

    allowed_ordering = (
        "name",
        "-name",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "name": "Name (A-Z)",
        "-name": "Name (Z-A)",
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class InstitutionCreateView(BaseCreateView):

    form_class = InstitutionForm

    template_name = (
        "academics/institution/form.html"
    )

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

    template_name = (
        "academics/institution/form.html"
    )

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

class DepartmentListView(BaseListView):

    model = Department

    selector = get_departments

    template_name = (
        "academics/department/list.html"
    )

    context_object_name = "departments"

    page_title = "Department Management"

    page_subtitle = "Manage departments"

    filter_parameters = (
        "institution",
        "is_active",
    )

    filter_choices = {
        "institution": Institution.objects.filter(
            is_active=True
        ).order_by("name"),
    }

    default_ordering = (
        "name",
    )

    allowed_ordering = (
        "name",
        "-name",
        "code",
        "-code",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "name": "Name (A-Z)",
        "-name": "Name (Z-A)",
        "code": "Code (A-Z)",
        "-code": "Code (Z-A)",
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class DepartmentCreateView(BaseCreateView):

    form_class = DepartmentForm

    template_name = (
        "academics/department/form.html"
    )

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

    template_name = (
        "academics/department/form.html"
    )

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

class CourseListView(BaseListView):

    model = Course

    selector = get_courses

    template_name = (
        "academics/course/list.html"
    )

    context_object_name = "courses"

    page_title = "Course Management"

    page_subtitle = "Manage academic courses"

    filter_parameters = (
        "department",
        "is_active",
    )

    filter_choices = {
        "department": Department.objects.filter(
            is_active=True
        ).select_related(
            "institution"
        ).order_by("name"),
    }

    default_ordering = (
        "name",
    )

    allowed_ordering = (
        "name",
        "-name",
        "code",
        "-code",
        "duration",
        "-duration",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "name": "Name (A-Z)",
        "-name": "Name (Z-A)",
        "code": "Code (A-Z)",
        "-code": "Code (Z-A)",
        "duration": "Duration",
        "-duration": "Duration",
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class CourseCreateView(BaseCreateView):

    form_class = CourseForm

    template_name = (
        "academics/course/form.html"
    )

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

    template_name = (
        "academics/course/form.html"
    )

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

class SemesterListView(BaseListView):

    model = Semester

    selector = get_semesters

    template_name = (
        "academics/semester/list.html"
    )

    context_object_name = "semesters"

    page_title = "Semester Management"

    page_subtitle = "Manage academic semesters"

    filter_parameters = (
        "course",
        "is_active",
    )

    filter_choices = {
        "course": Course.objects.filter(
            is_active=True
        ).select_related(
            "department"
        ).order_by("name"),
    }

    default_ordering = (
        "course__name",
        "semester_number",
    )

    allowed_ordering = (
        "semester_number",
        "-semester_number",
        "course__name",
        "-course__name",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "semester_number": "Semester Number",
        "-semester_number": (
            "Semester Number (Descending)"
        ),
        "course__name": "Course (A-Z)",
        "-course__name": "Course (Z-A)",
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class SemesterCreateView(BaseCreateView):
    """
    Create a new semester.
    """

    form_class = SemesterForm

    template_name = (
        "academics/semester/form.html"
    )

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

    template_name = (
        "academics/semester/form.html"
    )

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

class SubjectListView(BaseListView):

    model = Subject

    selector = get_subjects

    template_name = (
        "academics/subject/list.html"
    )

    context_object_name = "subjects"

    page_title = "Subject Management"

    page_subtitle = "Manage academic subjects"

    filter_parameters = (
        "semester",
        "is_active",
    )

    filter_choices = {
        "semester": Semester.objects.filter(
            is_active=True
        ).select_related(
            "course"
        ).order_by(
            "course__name",
            "semester_number",
        ),
    }

    default_ordering = (
        "name",
    )

    allowed_ordering = (
        "name",
        "-name",
        "code",
        "-code",
        "credits",
        "-credits",
        "created_at",
        "-created_at",
    )

    ordering_labels = {
        "name": "Name (A-Z)",
        "-name": "Name (Z-A)",
        "code": "Code (A-Z)",
        "-code": "Code (Z-A)",
        "credits": "Credits",
        "-credits": "Credits",
        "created_at": "Oldest First",
        "-created_at": "Newest First",
    }


class SubjectCreateView(BaseCreateView):
    """
    Create a new subject.
    """

    form_class = SubjectForm

    template_name = (
        "academics/subject/form.html"
    )

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

    template_name = (
        "academics/subject/form.html"
    )

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


# ==========================================================
# Institution CSV Import
# ==========================================================

class InstitutionCSVImportView(View):
    """
    Upload, validate, preview, and import Institution CSV files.
    """

    template_name = (
        "academics/csv/institution_import.html"
    )

    def get(self, request, *args, **kwargs):

        form = InstitutionCSVImportForm()

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):

        # ==================================================
        # CONFIRM IMPORT
        # ==================================================

        if request.POST.get("action") == "confirm_import":

            rows = request.session.get(
                "institution_csv_rows"
            )

            if not rows:

                messages.error(
                    request,
                    (
                        "No validated CSV data was found. "
                        "Please upload the CSV again."
                    ),
                )

                return redirect(
                    "academics:institution-import"
                )

            try:

                result = import_rows(
                    rows,
                    create_institution_from_csv_row,
                )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Import failed because one or more "
                        "records violate a database constraint. "
                        "No institutions were imported."
                    ),
                )

                return redirect(
                    "academics:institution-import"
                )

            except Exception:

                messages.error(
                    request,
                    (
                        "An unexpected error occurred while "
                        "importing the institutions. "
                        "No institutions were imported."
                    ),
                )

                return redirect(
                    "academics:institution-import"
                )

            request.session.pop(
                "institution_csv_rows",
                None,
            )

            messages.success(
                request,
                f"{result} institutions imported successfully.",
            )

            return redirect(
                "academics:institution-list"
            )

        # ==================================================
        # CSV UPLOAD
        # ==================================================

        form = InstitutionCSVImportForm(
            request.POST,
            request.FILES,
        )

        if not form.is_valid():

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                },
            )

        uploaded_file = form.cleaned_data[
            "csv_file"
        ]

        try:

            rows = read_institution_csv(
                uploaded_file
            )

            validate_institution_rows(
                rows
            )

        except (CSVImportError, ValueError) as exc:

            form.add_error(
                "csv_file",
                str(exc),
            )

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                },
            )

        request.session[
            "institution_csv_rows"
        ] = rows

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "preview_rows": rows,
                "preview_count": len(rows),
            },
        )


class InstitutionCSVTemplateView(View):
    """
    Download the fixed Institution CSV template.
    """

    def get(self, request, *args, **kwargs):

        from .csv.institution import (
            generate_institution_csv_template,
        )

        csv_content = (
            generate_institution_csv_template()
        )

        response = HttpResponse(
            csv_content,
            content_type="text/csv",
        )

        response["Content-Disposition"] = (
            'attachment; '
            'filename="institution_template.csv"'
        )

        return response

class DepartmentCSVImportView(View):
    """
    Upload, validate, preview, and import
    Department CSV files.
    """

    template_name = (
        "academics/csv/department_import.html"
    )

    def get(
        self,
        request,
        *args,
        **kwargs,
    ):

        form = InstitutionCSVImportForm()

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):

        if request.POST.get(
            "action"
        ) == "confirm_import":

            rows = request.session.get(
                "department_csv_rows"
            )

            if not rows:

                messages.error(
                    request,
                    (
                        "No validated CSV data was found. "
                        "Please upload the CSV again."
                    ),
                )

                return redirect(
                    "academics:department-import"
                )

            try:

                result = import_rows(
                    rows,
                    create_department_from_csv_row,
                )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Import failed because a database "
                        "constraint was violated. "
                        "No departments were imported."
                    ),
                )

                return redirect(
                    "academics:department-import"
                )

            except Exception:

                messages.error(
                    request,
                    (
                        "An unexpected error occurred "
                        "during import. "
                        "No departments were imported."
                    ),
                )

                return redirect(
                    "academics:department-import"
                )

            request.session.pop(
                "department_csv_rows",
                None,
            )

            messages.success(
                request,
                f"{result} departments imported successfully.",
            )

            return redirect(
                "academics:department-list"
            )

        form = InstitutionCSVImportForm(
            request.POST,
            request.FILES,
        )

        if not form.is_valid():

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                },
            )

        uploaded_file = form.cleaned_data[
            "csv_file"
        ]

        try:

            rows = read_department_csv(
                uploaded_file
            )

            validate_department_rows(
                rows
            )

        except (CSVImportError, ValueError) as exc:

            form.add_error(
                "csv_file",
                str(exc),
            )

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                },
            )

        request.session[
            "department_csv_rows"
        ] = rows

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "preview_rows": rows,
                "preview_count": len(rows),
            },
        )
class DepartmentCSVTemplateView(View):
    """
    Download the fixed Department CSV template.
    """

    def get(self, request, *args, **kwargs):

        from .csv.department import (
            generate_department_csv_template,
        )

        csv_content = (
            generate_department_csv_template()
        )

        response = HttpResponse(
            csv_content,
            content_type="text/csv",
        )

        response["Content-Disposition"] = (
            'attachment; '
            'filename="department_template.csv"'
        )

        return response

class CourseCSVImportView(View):
    """
    Upload, validate, preview, and import
    Course CSV files.
    """

    template_name = (
        "academics/csv/course_import.html"
    )

    def get(self, request, *args, **kwargs):

        form = InstitutionCSVImportForm()

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):

        if request.POST.get(
            "action"
        ) == "confirm_import":

            rows = request.session.get(
                "course_csv_rows"
            )

            if not rows:

                messages.error(
                    request,
                    (
                        "No validated CSV data was found. "
                        "Please upload the CSV again."
                    ),
                )

                return redirect(
                    "academics:course-import"
                )

            try:

                result = import_rows(
                    rows,
                    create_course_from_csv_row,
                )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Import failed because a database "
                        "constraint was violated. "
                        "No courses were imported."
                    ),
                )

                return redirect(
                    "academics:course-import"
                )

            except Exception:

                messages.error(
                    request,
                    (
                        "An unexpected error occurred "
                        "during import. "
                        "No courses were imported."
                    ),
                )

                return redirect(
                    "academics:course-import"
                )

            request.session.pop(
                "course_csv_rows",
                None,
            )

            messages.success(
                request,
                f"{result} courses imported successfully.",
            )

            return redirect(
                "academics:course-list"
            )

        form = InstitutionCSVImportForm(
            request.POST,
            request.FILES,
        )

        if not form.is_valid():

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                },
            )

        uploaded_file = form.cleaned_data[
            "csv_file"
        ]

        try:

            rows = read_course_csv(
                uploaded_file
            )

            validate_course_rows(
                rows
            )

        except (CSVImportError, ValueError) as exc:

            form.add_error(
                "csv_file",
                str(exc),
            )

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                },
            )

        request.session[
            "course_csv_rows"
        ] = rows

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "preview_rows": rows,
                "preview_count": len(rows),
            },
        )
class CourseCSVTemplateView(View):
    """
    Download the fixed Course CSV template.
    """

    def get(self, request, *args, **kwargs):

        from .csv.course import (
            generate_course_csv_template,
        )

        csv_content = (
            generate_course_csv_template()
        )

        response = HttpResponse(
            csv_content,
            content_type="text/csv",
        )

        response["Content-Disposition"] = (
            'attachment; '
            'filename="course_template.csv"'
        )

        return response


class SemesterCSVImportView(View):
    """
    Upload, validate, preview, and import
    Semester CSV files.
    """

    template_name = (
        "academics/csv/semester_import.html"
    )

    def get(self, request, *args, **kwargs):

        form = InstitutionCSVImportForm()

        return render(
            request,
            self.template_name,
            {"form": form},
        )

    def post(self, request, *args, **kwargs):

        if request.POST.get(
            "action"
        ) == "confirm_import":

            rows = request.session.get(
                "semester_csv_rows"
            )

            if not rows:

                messages.error(
                    request,
                    (
                        "No validated CSV data was found. "
                        "Please upload the CSV again."
                    ),
                )

                return redirect(
                    "academics:semester-import"
                )

            try:

                result = import_rows(
                    rows,
                    create_semester_from_csv_row,
                )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Import failed because a database "
                        "constraint was violated. "
                        "No semesters were imported."
                    ),
                )

                return redirect(
                    "academics:semester-import"
                )

            except Exception:

                messages.error(
                    request,
                    (
                        "An unexpected error occurred "
                        "during import. "
                        "No semesters were imported."
                    ),
                )

                return redirect(
                    "academics:semester-import"
                )

            request.session.pop(
                "semester_csv_rows",
                None,
            )

            messages.success(
                request,
                f"{result} semesters imported successfully.",
            )

            return redirect(
                "academics:semester-list"
            )

        form = InstitutionCSVImportForm(
            request.POST,
            request.FILES,
        )

        if not form.is_valid():

            return render(
                request,
                self.template_name,
                {"form": form},
            )

        uploaded_file = form.cleaned_data[
            "csv_file"
        ]

        try:

            rows = read_semester_csv(
                uploaded_file
            )

            validate_semester_rows(
                rows
            )

        except (CSVImportError, ValueError) as exc:

            form.add_error(
                "csv_file",
                str(exc),
            )

            return render(
                request,
                self.template_name,
                {"form": form},
            )

        request.session[
            "semester_csv_rows"
        ] = rows

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "preview_rows": rows,
                "preview_count": len(rows),
            },
        )

class SemesterCSVTemplateView(View):
    """
    Download the fixed Semester CSV template.
    """

    def get(self, request, *args, **kwargs):

        from .csv.semester import (
            generate_semester_csv_template,
        )

        csv_content = (
            generate_semester_csv_template()
        )

        response = HttpResponse(
            csv_content,
            content_type="text/csv",
        )

        response["Content-Disposition"] = (
            'attachment; '
            'filename="semester_template.csv"'
        )

        return response


class SubjectCSVImportView(View):
    """
    Upload, validate, preview, and import
    Subject CSV files.
    """

    template_name = (
        "academics/csv/subject_import.html"
    )

    def get(self, request, *args, **kwargs):

        form = InstitutionCSVImportForm()

        return render(
            request,
            self.template_name,
            {"form": form},
        )

    def post(self, request, *args, **kwargs):

        if request.POST.get(
            "action"
        ) == "confirm_import":

            rows = request.session.get(
                "subject_csv_rows"
            )

            if not rows:

                messages.error(
                    request,
                    (
                        "No validated CSV data was found. "
                        "Please upload the CSV again."
                    ),
                )

                return redirect(
                    "academics:subject-import"
                )

            try:

                result = import_rows(
                    rows,
                    create_subject_from_csv_row,
                )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Import failed because a database "
                        "constraint was violated. "
                        "No subjects were imported."
                    ),
                )

                return redirect(
                    "academics:subject-import"
                )

            except Exception:

                messages.error(
                    request,
                    (
                        "An unexpected error occurred "
                        "during import. "
                        "No subjects were imported."
                    ),
                )

                return redirect(
                    "academics:subject-import"
                )

            request.session.pop(
                "subject_csv_rows",
                None,
            )

            messages.success(
                request,
                f"{result} subjects imported successfully.",
            )

            return redirect(
                "academics:subject-list"
            )

        form = InstitutionCSVImportForm(
            request.POST,
            request.FILES,
        )

        if not form.is_valid():

            return render(
                request,
                self.template_name,
                {"form": form},
            )

        uploaded_file = form.cleaned_data[
            "csv_file"
        ]

        try:

            rows = read_subject_csv(
                uploaded_file
            )

            validate_subject_rows(
                rows
            )

        except (CSVImportError, ValueError) as exc:

            form.add_error(
                "csv_file",
                str(exc),
            )

            return render(
                request,
                self.template_name,
                {"form": form},
            )

        request.session[
            "subject_csv_rows"
        ] = rows

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "preview_rows": rows,
                "preview_count": len(rows),
            },
        )
class SubjectCSVTemplateView(View):
    """
    Download the fixed Subject CSV template.
    """

    def get(self, request, *args, **kwargs):

        from .csv.subject import (
            generate_subject_csv_template,
        )

        csv_content = (
            generate_subject_csv_template()
        )

        response = HttpResponse(
            csv_content,
            content_type="text/csv",
        )

        response["Content-Disposition"] = (
            'attachment; '
            'filename="subject_template.csv"'
        )

        return response