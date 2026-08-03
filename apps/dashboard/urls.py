from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardRedirectView.as_view(), name="redirect"),
    path(
        "admin/",
        views.AdminDashboardView.as_view(),
        name="admin",
    ),
    path(
        "teacher/",
        views.TeacherDashboardView.as_view(),
        name="teacher",
    ),
    path(
        "student/",
        views.StudentDashboardView.as_view(),
        name="student",
    ),
]
