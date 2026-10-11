"""Views for teacher-only AI document drafting and immediate export."""

import json
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.db.models import F

from apps.accounts.models import User
from apps.academics.models import Subject
from apps.teachers.models import TeachingAssignment

from .document_generation import (
    MAX_GENERATED_CHARACTERS,
    TeacherDocumentGenerationError,
    TeacherDocumentGenerationService,
    TeacherDocumentSourceService,
)
from .exporters import export_document


def _is_active_teacher(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "role", None) == User.Roles.TEACHER
    )


def _json_body(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


class TeacherDocumentGenerationPageView(LoginRequiredMixin, View):
    template_name = "rag/teacher/document_generation.html"

    def get(self, request, *args, **kwargs):
        if not _is_active_teacher(request.user):
            raise PermissionDenied("Only active teachers can access document generation.")

        assignment_rows = TeachingAssignment.objects.filter(
            teacher__user=request.user,
            is_active=True,
            semester_id=F("subject__semester_id"),
            course_id=F("subject__semester__course_id"),
        ).values_list("subject_id", flat=True)
        subjects = Subject.objects.filter(pk__in=assignment_rows).select_related(
            "semester", "semester__course"
        ).order_by("semester__course__name", "semester__semester_number", "name").distinct()
        source_documents = TeacherDocumentSourceService.for_teacher(request.user)
        return render(request, self.template_name, {
            "subjects": subjects,
            "source_documents": source_documents,
        })


class TeacherDocumentGenerateAPIView(LoginRequiredMixin, View):
    """Generate an in-memory draft; never persist generated content."""

    def post(self, request, *args, **kwargs):
        if not _is_active_teacher(request.user):
            return JsonResponse({"error": "Only active teachers can generate documents."}, status=403)
        payload = _json_body(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON request body."}, status=400)

        try:
            service = TeacherDocumentGenerationService()
            result = service.generate(
                user=request.user,
                subject_id=payload.get("subject_id"),
                instructions=payload.get("instructions"),
                source_document_ids=payload.get("source_document_ids", []),
            )
        except TeacherDocumentGenerationError as exc:
            message = str(exc)
            status = 403 if "access to this subject" in message or "Only active teachers" in message else 400
            return JsonResponse({"error": message}, status=status)
        except Exception:
            # Avoid returning provider/configuration details to the client.
            return JsonResponse({"error": "Document generation is temporarily unavailable."}, status=502)

        response = JsonResponse(result)
        response["Cache-Control"] = "no-store, private"
        return response


class TeacherDocumentExportAPIView(LoginRequiredMixin, View):
    """Export teacher-edited content directly to a download response."""

    def post(self, request, file_format, *args, **kwargs):
        if not _is_active_teacher(request.user):
            return JsonResponse({"error": "Only active teachers can export documents."}, status=403)
        payload = _json_body(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON request body."}, status=400)
        content = payload.get("content")
        if not isinstance(content, str) or not content.strip():
            return JsonResponse({"error": "Document content is required."}, status=400)
        if len(content) > MAX_GENERATED_CHARACTERS:
            return JsonResponse({"error": "Document content exceeds the allowed length."}, status=400)
        if file_format not in {"pdf", "docx", "pptx"}:
            return JsonResponse({"error": "Unsupported export format."}, status=400)
        filename = payload.get("filename", "teacher-document")
        if not isinstance(filename, str):
            filename = "teacher-document"
        filename = re.sub(r"[^A-Za-z0-9_-]+", "-", filename).strip("-_")[:60]
        if not filename:
            filename = "teacher-document"
        try:
            return export_document(
                content, file_format, filename=f"{filename}.{file_format}",
                title=payload.get("title") if isinstance(payload.get("title"), str) else None,
            )
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except Exception:
            return JsonResponse({"error": "Could not export this document. Please try again."}, status=500)
