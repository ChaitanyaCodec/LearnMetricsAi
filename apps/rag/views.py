import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.academics.csv import subject
from apps.academics.models import Subject
from apps.students.models import StudentEnrollment

from apps.documents.permissions import (
    is_documents_admin,
    student_can_access_subject,
    teacher_can_upload_for_subject,
)
from .conversations import (
    ConversationNotFoundError,
    ConversationService,
    ConversationServiceError,
    ConversationValidationError,
    can_access_conversation_subject,
)
from .services import (
    RagService,
    RagServiceError,
)


MAX_TOP_K = 20


class StudentRAGChatView(LoginRequiredMixin, View):
    """
    Render the Student RAG chat interface.

    Accessible subjects are derived from the authenticated
    student's active enrollments.

    This view only prepares page data. RAG generation and
    conversation operations continue to use the existing
    RAG API endpoints.
    """

    template_name = "rag/student_chat.html"

    def get(self, request, *args, **kwargs):
        semester_ids = (
            StudentEnrollment.objects
            .filter(
                student__user=request.user,
                status=StudentEnrollment.Status.ACTIVE,
                is_active=True,
            )
            .values_list(
                "semester_id",
                flat=True,
            )
        )

        subjects = (
            Subject.objects
            .filter(
                semester_id__in=semester_ids,
            )
            .select_related(
                "semester",
                "semester__course",
            )
            .order_by(
                "semester__course__name",
                "semester__semester_number",
                "name",
            )
        )

        return render(
            request,
            self.template_name,
            {
                "subjects": subjects,
            },
        )


class RagAskAPIView(LoginRequiredMixin, View):
    """
    Stateless RAG question endpoint.

    POST /rag/ask/
    """

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(
                request.body.decode("utf-8")
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {
                    "error": "Invalid JSON request body."
                },
                status=400,
            )

        question = payload.get("question")

        if not isinstance(question, str) or not question.strip():
            return JsonResponse(
                {
                    "error": "Question is required."
                },
                status=400,
            )

        subject_id = payload.get("subject_id")

        if (
            isinstance(subject_id, bool)
            or not isinstance(subject_id, int)
        ):
            return JsonResponse(
                {
                    "error": "subject_id must be an integer."
                },
                status=400,
            )

        top_k = self._validate_top_k(
            payload.get("top_k")
        )

        if isinstance(top_k, JsonResponse):
            return top_k

        try:
            subject = Subject.objects.get(
                pk=subject_id
            )
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

        try:
            result = RagService.answer_question_with_sources(
                user=request.user,
                question=question.strip(),
                subject=subject,
                top_k=top_k,
            )
        except RagServiceError as exc:
            return JsonResponse(
                {
                    "error": str(exc)
                },
                status=502,
            )

        return JsonResponse(
            {
                "answer": result.answer,
                "sources": self._serialize_sources(
                    result.chunks
                ),
            }
        )

    def _validate_top_k(self, value):
        if value is None:
            return 5

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
        ):
            return JsonResponse(
                {
                    "error": "top_k must be an integer."
                },
                status=400,
            )

        if value <= 0 or value > MAX_TOP_K:
            return JsonResponse(
                {
                    "error": (
                        f"top_k must be between 1 and "
                        f"{MAX_TOP_K}."
                    )
                },
                status=400,
            )

        return value

    def _can_access_subject(
        self,
        user,
        subject,
    ):
        return (
            is_documents_admin(user)
            or teacher_can_upload_for_subject(
                user,
                subject,
            )
            or student_can_access_subject(
                user,
                subject,
            )
        )

    def _serialize_sources(self, chunks):
        sources = []

        for chunk in chunks:
            document = getattr(
                chunk,
                "document",
                None,
            )

            sources.append(
                {
                    "document_id": (
                        document.id
                        if document is not None
                        else None
                    ),
                    "document_title": (
                        document.title
                        if document is not None
                        else None
                    ),
                    "chunk_id": chunk.id,
                    "page_number": getattr(
                        chunk,
                        "page_number",
                        None,
                    ),
                }
            )

        return sources


class ConversationListCreateAPIView(
    LoginRequiredMixin,
    View,
):
    """
    List and create persistent RAG conversations.

    GET  /rag/conversations/
    POST /rag/conversations/
    """

    conversation_service = ConversationService()

    def get(self, request, *args, **kwargs):
        conversations = (
            self.conversation_service.list_conversations(
                user=request.user
            )
        )

        return JsonResponse(
            {
                "conversations": [
                    self._serialize_conversation(
                        conversation
                    )
                    for conversation in conversations
                ]
            }
        )

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(
                request.body.decode("utf-8")
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {
                    "error": "Invalid JSON request body."
                },
                status=400,
            )

        subject_id = payload.get("subject_id")

        if (
            isinstance(subject_id, bool)
            or not isinstance(subject_id, int)
            or subject_id <= 0
        ):
            return JsonResponse(
                {
                    "error": (
                        "A positive integer subject_id "
                        "is required."
                    )
                },
                status=400,
            )

        title = payload.get("title", "")

        if not isinstance(title, str):
            return JsonResponse(
                {
                    "error": (
                        "Conversation title must be "
                        "a string."
                    )
                },
                status=400,
            )

        try:
            subject = Subject.objects.get(
                pk=subject_id
            )
        except Subject.DoesNotExist:
            return JsonResponse(
                {
                    "error": "Subject not found."
                },
                status=404,
            )

        if not can_access_conversation_subject(
            request.user,
            subject,
        ):
            return JsonResponse(
                {
                    "error": (
                        "You do not have access to "
                        "this subject."
                    )
                },
                status=403,
            )

        try:
            conversation = (
                self.conversation_service
                .create_conversation(
                    user=request.user,
                    subject=subject,
                    title=title,
                )
            )
        except ConversationValidationError as exc:
            return JsonResponse(
                {
                    "error": str(exc)
                },
                status=400,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "error": str(exc)
                },
                status=500,
            )

        return JsonResponse(
            self._serialize_conversation(
                conversation
            ),
            status=201,
        )

    def _serialize_conversation(
        self,
        conversation,
    ):
        return {
            "id": str(conversation.id),
            "subject_id": conversation.subject_id,
            "subject_name": conversation.subject.name,
            "title": conversation.title,
            "is_active": conversation.is_active,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }


class ConversationDetailAPIView(
    LoginRequiredMixin,
    View,
):
    """
    Return one conversation with its messages.

    GET /rag/conversations/<conversation_id>/
    """

    conversation_service = ConversationService()

    def get(
        self,
        request,
        conversation_id,
        *args,
        **kwargs,
    ):
        try:
            conversation = (
                self.conversation_service
                .get_conversation(
                    user=request.user,
                    conversation_id=conversation_id,
                )
            )
        except ConversationNotFoundError as exc:
            return JsonResponse(
                {
                    "error": str(exc)
                },
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "error": str(exc)
                },
                status=500,
            )

        return JsonResponse(
            self._serialize_conversation(
                conversation
            )
        )

    def _serialize_conversation(
        self,
        conversation,
    ):
        return {
            "id": str(conversation.id),
            "subject_id": conversation.subject_id,
            "subject_name": conversation.subject.name,
            "title": conversation.title,
            "is_active": conversation.is_active,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "messages": [
                self._serialize_message(message)
                for message in conversation.messages.all()
            ],
        }

    def _serialize_message(
        self,
        message,
    ):
        return {
            "id": str(message.id),
            "conversation_id": str(
                message.conversation_id
            ),
            "role": message.role,
            "content": message.content,
            "sequence": message.sequence,
            "metadata": message.metadata,
            "created_at": message.created_at.isoformat(),
        }


class ConversationMessageAPIView(
    LoginRequiredMixin,
    View,
):
    """
    Send a question inside an existing conversation.

    POST /rag/conversations/<conversation_id>/messages/
    """

    conversation_service = ConversationService()

    def post(
        self,
        request,
        conversation_id,
        *args,
        **kwargs,
    ):
        try:
            payload = json.loads(
                request.body.decode("utf-8")
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {
                    "error": "Invalid JSON request body."
                },
                status=400,
            )

        question = payload.get("question")

        if not isinstance(question, str) or not question.strip():
            return JsonResponse(
                {
                    "error": "Question is required."
                },
                status=400,
            )

        top_k = self._validate_top_k(
            payload.get("top_k")
        )

        if isinstance(top_k, JsonResponse):
            return top_k

        try:
            conversation = (
                self.conversation_service
                .get_conversation(
                    user=request.user,
                    conversation_id=conversation_id,
                )
            )
        except ConversationNotFoundError as exc:
            return JsonResponse(
                {
                    "error": str(exc)
                },
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "error": str(exc)
                },
                status=500,
            )

        if not can_access_conversation_subject(
            request.user,
            conversation.subject,
        ):
            return JsonResponse(
                {
                    "error": (
                        "You do not have access to "
                        "this conversation."
                    )
                },
                status=403,
            )

        history = (
            self.conversation_service
            .get_conversation_history(
                user=request.user,
                conversation_id=conversation_id,
            )
        )

        user_message = (
            self.conversation_service
            .add_user_message(
                user=request.user,
                conversation_id=conversation_id,
                content=question.strip(),
            )
        )

        try:
            rag_service = RagService()

            result = rag_service.answer_question_with_sources(
                user=request.user,
                question=question,
                subject=conversation.subject,
                conversation_history=history,
            )
        except RagServiceError as exc:
            return JsonResponse(
                {
                    "error": str(exc),
                    "user_message_id": str(
                        user_message.id
                    ),
                },
                status=502,
            )

        serialized_sources = (
            self._serialize_sources(
                result.chunks
            )
        )

        assistant_message = (
            self.conversation_service
            .add_assistant_message(
                user=request.user,
                conversation_id=conversation_id,
                content=result.answer,
                sources=serialized_sources,
            )
        )

        return JsonResponse(
            {
                "user_message": (
                    self._serialize_message(
                        user_message
                    )
                ),
                "assistant_message": (
                    self._serialize_message(
                        assistant_message
                    )
                ),
                "answer": result.answer,
                "sources": serialized_sources,
            }
        )

    def _validate_top_k(self, value):
        if value is None:
            return 5

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
        ):
            return JsonResponse(
                {
                    "error": "top_k must be an integer."
                },
                status=400,
            )

        if value <= 0 or value > MAX_TOP_K:
            return JsonResponse(
                {
                    "error": (
                        f"top_k must be between 1 and "
                        f"{MAX_TOP_K}."
                    )
                },
                status=400,
            )

        return value

    def _serialize_sources(self, chunks):
        sources = []

        for chunk in chunks:
            document = getattr(
                chunk,
                "document",
                None,
            )

            sources.append(
                {
                    "document_id": (
                        document.id
                        if document is not None
                        else None
                    ),
                    "document_title": (
                        document.title
                        if document is not None
                        else None
                    ),
                    "chunk_id": chunk.id,
                    "page_number": getattr(
                        chunk,
                        "page_number",
                        None,
                    ),
                }
            )

        return sources

    def _serialize_message(
        self,
        message,
    ):
        return {
            "id": str(message.id),
            "conversation_id": str(
                message.conversation_id
            ),
            "role": message.role,
            "content": message.content,
            "sequence": message.sequence,
            "metadata": message.metadata,
            "created_at": message.created_at.isoformat(),
        }