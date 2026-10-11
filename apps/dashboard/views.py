from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.mixins import (
    AdminRequiredMixin,
    TeacherRequiredMixin,
    StudentRequiredMixin,
)
from .services import (
    get_admin_dashboard_statistics,
    get_student_dashboard_statistics,
    get_teacher_dashboard_statistics,
)


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.role == request.user.Roles.ADMIN:
            return redirect("dashboard:admin")
        if request.user.role == request.user.Roles.TEACHER:
            return redirect("dashboard:teacher")
        if request.user.role == request.user.Roles.STUDENT:
            return redirect("dashboard:student")
        return redirect("accounts:login")


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = "dashboard/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard"] = get_admin_dashboard_statistics()
        return context


class TeacherDashboardView(LoginRequiredMixin, TeacherRequiredMixin, TemplateView):
    template_name = "dashboard/teacher_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard"] = get_teacher_dashboard_statistics(self.request.user)
        return context


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    template_name = "dashboard/student_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard"] = get_student_dashboard_statistics(self.request.user)
        return context
