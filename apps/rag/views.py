import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from apps.accounts.models import User
from apps.academics.models import Subject
from apps.documents.permissions import (
    is_documents_admin,
    student_can_access_subject,
    teacher_can_upload_for_subject,
)

from .services import RagService, RagServiceError


class RagBaseView(LoginRequiredMixin, View):
    """
    Base view for authenticated RAG API endpoints.
    """

    login_url = "/auth/login/"


class RagAskAPIView(RagBaseView):
    """
    Ask the LearnMetrics AI assistant a question.

    POST /rag/ask/

    Request:
    {
        "question": "What is normalization in DBMS?",
        "subject_id": 1,
        "top_k": 5
    }

    Response:
    {
        "answer": "....",
        "sources": [
            {
                "document_id": 12,
                "document_title": "DBMS Notes",
                "chunk_id": 45,
                "page_number": 7
            }
        ]
    }
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        payload = self._parse_json(request)

        if payload is None:
            return JsonResponse(
                {
                    "error": "Invalid JSON request body."
                },
                status=400,
            )

        validation_error = self._validate_payload(payload)

        if validation_error is not None:
            return JsonResponse(
                {
                    "error": validation_error
                },
                status=400,
            )

        question = payload["question"].strip()
        subject_id = payload["subject_id"]
        top_k = payload.get("top_k")

        try:
            subject = Subject.objects.get(pk=subject_id)
        except Subject.DoesNotExist:
            return JsonResponse(
                {
                    "error": "Subject not found."
                },
                status=404,
            )

        if not self._can_access_subject(
            request.user,
            subject,
        ):
            return JsonResponse(
                {
                    "error": "You do not have access to this subject."
                },
                status=403,
            )

        rag_service = RagService()

        try:
            result = rag_service.answer_question_with_sources(
                user=request.user,
                question=question,
                subject=subject,
                top_k=top_k,
            )
        except RagServiceError:
            return JsonResponse(
                {
                    "error": "Unable to generate an answer at this time."
                },
                status=500,
            )
        except Exception:
            return JsonResponse(
                {
                    "error": (
                        "An unexpected error occurred while "
                        "processing the question."
                    )
                },
                status=500,
            )

        return JsonResponse(
            {
                "answer": result.answer,
                "sources": self._serialize_sources(
                    result.chunks
                ),
            },
            status=200,
        )

    @staticmethod
    def _parse_json(request):
        try:
            body = request.body.decode("utf-8")
            return json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    @staticmethod
    def _validate_payload(payload):
        if not isinstance(payload, dict):
            return "Request body must be a JSON object."

        question = payload.get("question")

        if not isinstance(question, str):
            return "Question must be a string."

        if not question.strip():
            return "Question cannot be empty."

        if "subject_id" not in payload:
            return "subject_id is required."

        subject_id = payload["subject_id"]

        if (
            isinstance(subject_id, bool)
            or not isinstance(subject_id, int)
        ):
            return "subject_id must be an integer."

        if subject_id <= 0:
            return "subject_id must be greater than zero."

        if "top_k" in payload:
            top_k = payload["top_k"]

            if (
                isinstance(top_k, bool)
                or not isinstance(top_k, int)
            ):
                return "top_k must be an integer."

            if top_k <= 0:
                return "top_k must be greater than zero."

        return None

    @staticmethod
    def _can_access_subject(user, subject):
        if is_documents_admin(user):
            return True

        if (
            user.is_authenticated
            and user.is_active
            and user.role == User.Roles.TEACHER
        ):
            return teacher_can_upload_for_subject(
                user,
                subject,
            )

        if (
            user.is_authenticated
            and user.is_active
            and user.role == User.Roles.STUDENT
        ):
            return student_can_access_subject(
                user,
                subject,
            )

        return False

    @staticmethod
    def _serialize_sources(chunks):
        sources = []

        for chunk in chunks:
            document_version = getattr(
                chunk,
                "document_version",
                None,
            )

            document = getattr(
                document_version,
                "document",
                None,
            )

            if document is None:
                continue

            sources.append(
                {
                    "document_id": document.id,
                    "document_title": document.title,
                    "chunk_id": chunk.id,
                    "page_number": chunk.page_number,
                }
            )

        return sources