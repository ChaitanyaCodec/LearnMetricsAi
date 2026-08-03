from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.mixins import (
    AdminRequiredMixin,
    TeacherRequiredMixin,
    StudentRequiredMixin,
)


class DashboardRedirectView(LoginRequiredMixin, View):
    """
    Redirect authenticated users to their role-based dashboard.
    """

    def get(self, request, *args, **kwargs):

        if request.user.role == request.user.Roles.ADMIN:
            return redirect("dashboard:admin")

        elif request.user.role == request.user.Roles.TEACHER:
            return redirect("dashboard:teacher")

        elif request.user.role == request.user.Roles.STUDENT:
            return redirect("dashboard:student")

        return redirect("accounts:login")


class AdminDashboardView(
    LoginRequiredMixin,
    AdminRequiredMixin,
    TemplateView,
):
    """
    Administrator Dashboard
    """

    template_name = "dashboard/admin_dashboard.html"


class TeacherDashboardView(
    LoginRequiredMixin,
    TeacherRequiredMixin,
    TemplateView,
):
    """
    Teacher Dashboard
    """

    template_name = "dashboard/teacher_dashboard.html"


class StudentDashboardView(
    LoginRequiredMixin,
    StudentRequiredMixin,
    TemplateView,
):
    """
    Student Dashboard
    """

    template_name = "dashboard/student_dashboard.html"