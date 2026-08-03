from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import View

from apps.accounts.mixins import (
    AdminRequiredMixin,
    StudentRequiredMixin,
    TeacherRequiredMixin,
)


class AdminDashboardView(
    LoginRequiredMixin,
    AdminRequiredMixin,
    View,
):

    def get(self, request):
        return HttpResponse("Administrator Dashboard")


class TeacherDashboardView(
    LoginRequiredMixin,
    TeacherRequiredMixin,
    View,
):

    def get(self, request):
        return HttpResponse("Teacher Dashboard")


class StudentDashboardView(
    LoginRequiredMixin,
    StudentRequiredMixin,
    View,
):

    def get(self, request):
        return HttpResponse("Student Dashboard")
