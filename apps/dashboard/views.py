from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.db.models import Q, Count, Max
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.mixins import (
    AdminRequiredMixin,
    TeacherRequiredMixin,
    StudentRequiredMixin,
)
from apps.accounts.models import User as AccountUser
from apps.academics.models import Course, Subject
from apps.documents.models import Document, DocumentVersion, DocumentViewEvent
from apps.documents.permissions import can_view_document, student_can_access_subject, teacher_can_upload_for_subject
from apps.students.models import Student, StudentEnrollment
from apps.teachers.models import Teacher, TeachingAssignment

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

        # Scope analytics to documents this teacher owns or is assigned to teach.
        engagement_documents = (
            Document.objects.filter(
                Q(created_by=self.request.user)
                | Q(subject__teaching_assignments__teacher__user=self.request.user,
                    subject__teaching_assignments__is_active=True),
                is_active=True,
                status=Document.Status.APPROVED,
                published_version__isnull=False,
                published_version__is_active=True,
                published_version__review_status=DocumentVersion.ReviewStatus.APPROVED,
                published_version__processing_status=DocumentVersion.ProcessingStatus.COMPLETED,
            )
            .select_related("subject", "published_version")
            .annotate(
                preview_count=Count(
                    "view_events",
                    filter=Q(view_events__event_type=DocumentViewEvent.EventType.PREVIEW),
                ),
                download_count=Count(
                    "view_events",
                    filter=Q(view_events__event_type=DocumentViewEvent.EventType.DOWNLOAD),
                ),
                unique_students=Count("view_events__student", distinct=True),
                last_viewed_at=Max("view_events__viewed_at"),
            )
            .distinct()
            .order_by("subject__name", "title")
        )
        engagement_rows = []
        for document in engagement_documents:
            latest_events = (
                DocumentViewEvent.objects.filter(document=document)
                .select_related("student")
                .order_by("student_id", "-viewed_at")
            )
            latest_by_student = {}
            for event in latest_events:
                if event.student_id not in latest_by_student:
                    latest_by_student[event.student_id] = event
            engagement_rows.append({
                "document": document,
                "preview_count": document.preview_count,
                "download_count": document.download_count,
                "total_events": document.preview_count + document.download_count,
                "unique_students": document.unique_students,
                "last_viewed_at": document.last_viewed_at,
                "student_events": sorted(
                    latest_by_student.values(),
                    key=lambda event: event.viewed_at,
                    reverse=True,
                ),
            })
        context["document_engagement_rows"] = engagement_rows
        context["document_engagement_totals"] = {
            "documents": len(engagement_rows),
            "previews": sum(row["preview_count"] for row in engagement_rows),
            "downloads": sum(row["download_count"] for row in engagement_rows),
            "students_reached": len({
                event.student_id
                for row in engagement_rows
                for event in row["student_events"]
            }),
        }
        return context


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    template_name = "dashboard/student_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard"] = get_student_dashboard_statistics(self.request.user)
        return context


class UniversalSearchView(LoginRequiredMixin, View):
    """Search resources visible to the current authenticated user."""

    max_results = 12

    def get(self, request, *args, **kwargs):
        query = (request.GET.get("q") or "").strip()[:100]
        if len(query) < 2:
            return JsonResponse({"query": query, "results": []})

        user = request.user
        results = []

        def add(category, title, subtitle, url):
            if len(results) < self.max_results:
                results.append({"category": category, "title": str(title), "subtitle": str(subtitle), "url": url})

        # Academic resources are filtered by role before search results are emitted.
        if user.role == AccountUser.Roles.ADMIN:
            students = Student.objects.filter(
                Q(student_id__icontains=query) | Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) | Q(user__email__icontains=query)
            ).select_related("user")[:5]
            for student in students:
                add("Student", student.user.full_name or student.user.email, student.student_id, reverse("students:student-detail", args=[student.pk]))

            teachers = Teacher.objects.filter(
                Q(employee_id__icontains=query) | Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) | Q(user__email__icontains=query)
            ).select_related("user")[:5]
            for teacher in teachers:
                add("Teacher", teacher.user.full_name or teacher.user.email, teacher.employee_id, reverse("teachers:teacher-detail", args=[teacher.pk]))

            courses = Course.objects.filter(Q(name__icontains=query) | Q(code__icontains=query), is_active=True)[:5]
            for course in courses:
                add("Course", course.name, course.code, reverse("academics:course-list") + "?" + urlencode({"search": query}))

            subjects = Subject.objects.filter(Q(name__icontains=query) | Q(code__icontains=query), is_active=True)[:5]
            for subject in subjects:
                add("Subject", subject.name, subject.code, reverse("academics:subject-list") + "?" + urlencode({"search": query}))

            documents = Document.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query), is_active=True
            ).select_related("subject")[:8]
        elif user.role == AccountUser.Roles.TEACHER:
            assigned_subject_ids = TeachingAssignment.objects.filter(
                teacher__user=user, is_active=True
            ).values_list("subject_id", flat=True)
            subjects = Subject.objects.filter(
                Q(name__icontains=query) | Q(code__icontains=query),
                pk__in=assigned_subject_ids, is_active=True
            )[:8]
            for subject in subjects:
                add("Subject", subject.name, subject.code, reverse("rag:teacher:chat"))
            documents = Document.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                Q(created_by=user) | Q(subject_id__in=assigned_subject_ids, status=Document.Status.APPROVED, published_version__isnull=False),
                is_active=True
            ).select_related("subject")[:8]
        elif user.role == AccountUser.Roles.STUDENT:
            enrollment_ids = StudentEnrollment.objects.filter(
                student__user=user, status=StudentEnrollment.Status.ACTIVE, is_active=True
            ).values_list("semester_id", flat=True)
            subjects = Subject.objects.filter(
                Q(name__icontains=query) | Q(code__icontains=query),
                semester_id__in=enrollment_ids, is_active=True
            )[:8]
            for subject in subjects:
                add("Subject", subject.name, subject.code, reverse("rag:student-chat"))
            visible_subject_ids = Subject.objects.filter(semester_id__in=enrollment_ids, is_active=True).values_list("id", flat=True)
            documents = Document.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                subject_id__in=visible_subject_ids, status=Document.Status.APPROVED,
                published_version__isnull=False, is_active=True,
                published_version__is_active=True,
                published_version__review_status=DocumentVersion.ReviewStatus.APPROVED,
                published_version__processing_status=DocumentVersion.ProcessingStatus.COMPLETED,
            ).select_related("subject")[:8]
        else:
            return JsonResponse({"query": query, "results": []})

        for document in documents:
            if can_view_document(user, document):
                add("Document", document.title, document.subject.name, reverse("documents:detail", args=[document.pk]))

        return JsonResponse({"query": query, "results": results[:self.max_results]})
