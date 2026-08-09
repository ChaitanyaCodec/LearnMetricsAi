from django.urls import path

from . import views
app_name = "academics"

urlpatterns = [
    path(
        "",
        views.AcademicsDashboardView.as_view(),
        name="dashboard",
    ),

    # ==========================================================
    # Institution
    # ==========================================================

 

    path(
        "institutions/",
        views.InstitutionListView.as_view(),
        name="institution-list",
    ),

    path(
        "institutions/create/",
        views.InstitutionCreateView.as_view(),
        name="institution-create",
    ),

    path(
        "institutions/import/",
        views.InstitutionCSVImportView.as_view(),
        name="institution-import",
    ),

    path(
        "institutions/<int:pk>/update/",
        views.InstitutionUpdateView.as_view(),
        name="institution-update",
    ),
    path(
        "institutions/import/template/",
        views.InstitutionCSVTemplateView.as_view(),
        name="institution-csv-template",
    ),

    path(
        "institutions/<int:pk>/delete/",
        views.InstitutionDeleteView.as_view(),
        name="institution-delete",
    ),

    # ==========================================================
    # Department
    # ==========================================================

    path(
        "departments/",
        views.DepartmentListView.as_view(),
        name="department-list",
    ),

    path(
        "departments/create/",
        views.DepartmentCreateView.as_view(),
        name="department-create",
    ),

    path(
        "departments/<int:pk>/update/",
        views.DepartmentUpdateView.as_view(),
        name="department-update",
    ),

    path(
        "departments/<int:pk>/delete/",
        views.DepartmentDeleteView.as_view(),
        name="department-delete",
    ),
    path(
        "departments/import/",
        views.DepartmentCSVImportView.as_view(),
        name="department-import",
    ),
    path(
        "departments/import/template/",
        views.DepartmentCSVTemplateView.as_view(),
        name="department-csv-template",
    ),

# ==========================================================
# Course
# ==========================================================

    path(
        "courses/",
        views.CourseListView.as_view(),
        name="course-list",
    ),

    path(
        "courses/create/",
        views.CourseCreateView.as_view(),
        name="course-create",
    ),

    path(
        "courses/<int:pk>/update/",
        views.CourseUpdateView.as_view(),
        name="course-update",
    ),

    path(
        "courses/<int:pk>/delete/",
        views.CourseDeleteView.as_view(),
        name="course-delete",
    ),

    path(
        "courses/import/",
        views.CourseCSVImportView.as_view(),
        name="course-import",
    ),

    path(
        "courses/import/template/",
        views.CourseCSVTemplateView.as_view(),
        name="course-csv-template",
    ),
    # ==========================================================
    # Semester
    # ==========================================================

    path(
        "semesters/",
        views.SemesterListView.as_view(),
        name="semester-list",
    ),

    path(
        "semesters/create/",
        views.SemesterCreateView.as_view(),
        name="semester-create",
    ),

    path(
        "semesters/<int:pk>/update/",
        views.SemesterUpdateView.as_view(),
        name="semester-update",
    ),

    path(
        "semesters/<int:pk>/delete/",
        views.SemesterDeleteView.as_view(),
        name="semester-delete",
    ),

    path(
        "semesters/import/",
        views.SemesterCSVImportView.as_view(),
        name="semester-import",
    ),

    path(
        "semesters/import/template/",
        views.SemesterCSVTemplateView.as_view(),
        name="semester-csv-template",
    ),
    # ==========================================================
    # Subject
    # ==========================================================

    path(
        "subjects/",
        views.SubjectListView.as_view(),
        name="subject-list",
    ),

    path(
        "subjects/create/",
        views.SubjectCreateView.as_view(),
        name="subject-create",
    ),

    path(
        "subjects/<int:pk>/update/",
        views.SubjectUpdateView.as_view(),
        name="subject-update",
    ),

    path(
        "subjects/<int:pk>/delete/",
        views.SubjectDeleteView.as_view(),
        name="subject-delete",
    ),
    path(
        "subjects/import/",
        views.SubjectCSVImportView.as_view(),
        name="subject-import",
    ),

    path(
        "subjects/import/template/",
        views.SubjectCSVTemplateView.as_view(),
        name="subject-csv-template",
    ),

]