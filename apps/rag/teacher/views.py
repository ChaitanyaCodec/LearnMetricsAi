
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.shortcuts import render
from django.views import View

from apps.accounts.models import User
from apps.academics.models import Subject
from apps.teachers.models import TeachingAssignment


class TeacherRAGChatView(LoginRequiredMixin, View):
    """
    Render the dedicated teacher RAG assistant.

    Teachers can see only subjects associated with their
    active teaching assignments.
    """

    template_name = "rag/teacher/chat.html"

    def get(self, request, *args, **kwargs):
        user = request.user

        if (
            not user.is_active
            or user.role != User.Roles.TEACHER
        ):
            raise PermissionDenied(
                "Only active teachers can access this page."
            )

        assigned_subject_ids = (
            TeachingAssignment.objects
            .filter(
                teacher__user=user,
                is_active=True,
                semester_id=F("subject__semester_id"),
                course_id=F("subject__semester__course_id"),
            )
            .values_list("subject_id", flat=True)
        )

        subjects = (
            Subject.objects
            .filter(pk__in=assigned_subject_ids)
            .select_related(
                "semester",
                "semester__course",
            )
            .order_by(
                "semester__course__name",
                "semester__semester_number",
                "name",
            )
            .distinct()
        )

        return render(
            request,
            self.template_name,
            {
                "subjects": subjects,
                "assistant_mode": "teacher",
            },
        )
