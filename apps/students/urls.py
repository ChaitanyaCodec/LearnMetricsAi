from django.urls import path

from . import views


app_name = "students"


urlpatterns = [
    # ======================================================
    # Student Management
    # ======================================================

    path(
        "",
        views.StudentManagementDashboardView.as_view(),
        name="dashboard",
    ),

    path(
        "students/",
        views.StudentListView.as_view(),
        name="student-list",
    ),

    path(
        "students/create/",
        views.StudentCreateView.as_view(),
        name="student-create",
    ),

    path(
        "students/<int:pk>/update/",
        views.StudentUpdateView.as_view(),
        name="student-update",
    ),

    path(
        "students/import/",
        views.StudentBulkImportView.as_view(),
        name="student-import",
    ),
    path(
        "students/import/template/",
        views.StudentCSVTemplateView.as_view(),
        name="student-import-template",
    ),

    # ======================================================
    # Enrollment Management
    # ======================================================

    path(
        "enrollments/",
        views.StudentEnrollmentListView.as_view(),
        name="enrollment-list",
    ),

    path(
        "enrollments/create/",
        views.StudentEnrollmentCreateView.as_view(),
        name="enrollment-create",
    ),

    path(
        "enrollments/<int:pk>/update/",
        views.StudentEnrollmentUpdateView.as_view(),
        name="enrollment-update",
    ),
]