from django.urls import path

from . import views


app_name = "teachers"


urlpatterns = [

    # ======================================================
    # Teacher Management
    # ======================================================

    path(
        "",
        views.TeacherManagementDashboardView.as_view(),
        name="dashboard",
    ),

    path(
        "teachers/",
        views.TeacherListView.as_view(),
        name="teacher-list",
    ),

    path(
        "teachers/create/",
        views.TeacherCreateView.as_view(),
        name="teacher-create",
    ),

    path(
        "teachers/<int:pk>/update/",
        views.TeacherUpdateView.as_view(),
        name="teacher-update",
    ),

    # ======================================================
    # Teaching Assignments
    # ======================================================

    path(
        "assignments/",
        views.TeachingAssignmentListView.as_view(),
        name="assignment-list",
    ),

    path(
        "assignments/create/",
        views.TeachingAssignmentCreateView.as_view(),
        name="assignment-create",
    ),

    path(
        "assignments/<int:pk>/update/",
        views.TeachingAssignmentUpdateView.as_view(),
        name="assignment-update",
    ),
    path(
        "api/semesters/",
        views.SemesterOptionsView.as_view(),
        name="semester-options",
        ),

    path(
        "api/subjects/",
        views.SubjectOptionsView.as_view(),
        name="subject-options",
    ),
]