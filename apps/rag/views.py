import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

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
from .guidance import QueryGuidanceService
from .services import (
    RagClarificationRequiredError,
    RagNoRelevantContextError,
    RagService,
    RagServiceError,
)


MAX_TOP_K = 20


class StudentRAGChatView(LoginRequiredMixin, View):
    """
    Render the Student RAG chat interface.

    Accessible subjects are derived from the authenticated
    student's active enrollments.
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

    guidance_service = QueryGuidanceService()

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(
                request.body.decode("utf-8")
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": "Invalid JSON request body.",
                },
                status=400,
            )

        question = payload.get("question")

        if not isinstance(question, str) or not question.strip():
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": "Question is required.",
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
                    "status": "ERROR",
                    "error": "subject_id must be an integer.",
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
                    "status": "ERROR",
                    "error": "Subject not found.",
                },
                status=404,
            )

        if not self._can_access_subject(
            request.user,
            subject,
        ):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": "You do not have access to this subject.",
                },
                status=403,
            )

        try:
            rag_service = RagService(
                enable_llm_reframing=True
            )

            result = rag_service.answer_question_with_sources(
                user=request.user,
                question=question.strip(),
                subject=subject,
                top_k=top_k,
            )
        except RagClarificationRequiredError:
            guidance = self.guidance_service.build(
                question=question.strip(),
                reason=QueryGuidanceService.CLARIFICATION,
                subject=subject,
            )

            return JsonResponse(
                {
                    "status": "CLARIFICATION",
                    "guidance": {
                        "message": guidance.message,
                        "suggestions": list(
                            guidance.suggestions
                        ),
                        "reason": guidance.reason,
                    },
                }
            )
        except RagNoRelevantContextError:
            guidance = self.guidance_service.build(
                question=question.strip(),
                reason=(
                    QueryGuidanceService.NO_RELEVANT_CONTEXT
                ),
                subject=subject,
            )

            return JsonResponse(
                {
                    "status": "NO_RELEVANT_CONTEXT",
                    "guidance": {
                        "message": guidance.message,
                        "suggestions": list(
                            guidance.suggestions
                        ),
                        "reason": guidance.reason,
                    },
                }
            )
        except RagServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=502,
            )

        return JsonResponse(
            {
                "status": "ANSWER",
                "answer": result.answer,
                "sources": self._serialize_sources(
                    result.chunks
                ),
            }
        )

    def _validate_top_k(self, value):
        if value is None:
            return None

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
        ):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": "top_k must be an integer.",
                },
                status=400,
            )

        if value <= 0:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": "top_k must be greater than zero.",
                },
                status=400,
            )

        if value > MAX_TOP_K:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": (
                        f"top_k cannot exceed {MAX_TOP_K}."
                    ),
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

    @staticmethod
    def _serialize_sources(chunks):
        sources = []

        for chunk in chunks:
            document_version = getattr(
                chunk,
                "document_version",
                None,
            )

            if document_version is None:
                continue

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
        conversations = [
            conversation
            for conversation in self.conversation_service.list_conversations(
                user=request.user
            )
            if can_access_conversation_subject(
                request.user,
                conversation.subject,
            )
        ]

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
                    "status": "ERROR",
                    "error": "Invalid JSON request body.",
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
                    "status": "ERROR",
                    "error": (
                        "A positive integer subject_id "
                        "is required."
                    ),
                },
                status=400,
            )

        title = payload.get("title", "")

        if not isinstance(title, str):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": (
                        "Conversation title must be "
                        "a string."
                    ),
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
                    "status": "ERROR",
                    "error": "Subject not found.",
                },
                status=404,
            )

        if not can_access_conversation_subject(
            request.user,
            subject,
        ):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": (
                        "You do not have access to "
                        "this subject."
                    ),
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
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=400,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=500,
            )

        return JsonResponse(
            {
                "conversation": self._serialize_conversation(
                    conversation
                ),
            },
            status=201,
        )

    @staticmethod
    def _serialize_conversation(
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
    Conversation management endpoint.

    GET:
        Return one active conversation with messages.

    PATCH:
        Rename one active conversation.

    DELETE:
        Soft-delete one active conversation.

    Endpoint:
        /rag/conversations/<conversation_id>/
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
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=500,
            )

        if not can_access_conversation_subject(
            request.user,
            conversation.subject,
        ):
            return self._access_denied_response()

        return JsonResponse(
            {
                "conversation": self._serialize_conversation(
                    conversation
                ),
            }
        )

    def patch(
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
                    "status": "ERROR",
                    "error": "Invalid JSON request body.",
                },
                status=400,
            )

        title = payload.get("title")

        if not isinstance(title, str):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": (
                        "Conversation title must be "
                        "a string."
                    ),
                },
                status=400,
            )

        try:
            existing_conversation = (
                self.conversation_service.get_conversation(
                    user=request.user,
                    conversation_id=conversation_id,
                )
            )
        except ConversationNotFoundError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=500,
            )

        if not can_access_conversation_subject(
            request.user,
            existing_conversation.subject,
        ):
            return self._access_denied_response()

        try:
            conversation = (
                self.conversation_service
                .rename_conversation(
                    user=request.user,
                    conversation_id=conversation_id,
                    title=title,
                )
            )
        except ConversationValidationError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=400,
            )
        except ConversationNotFoundError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=500,
            )

        return JsonResponse(
            {
                "status": "UPDATED",
                "conversation": self._serialize_conversation(
                    conversation
                ),
            }
        )

    def delete(
        self,
        request,
        conversation_id,
        *args,
        **kwargs,
    ):
        try:
            existing_conversation = (
                self.conversation_service.get_conversation(
                    user=request.user,
                    conversation_id=conversation_id,
                )
            )
        except ConversationNotFoundError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=500,
            )

        if not can_access_conversation_subject(
            request.user,
            existing_conversation.subject,
        ):
            return self._access_denied_response()

        try:
            conversation = (
                self.conversation_service
                .delete_conversation(
                    user=request.user,
                    conversation_id=conversation_id,
                )
            )
        except ConversationNotFoundError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=500,
            )

        return JsonResponse(
            {
                "status": "DELETED",
                "conversation_id": str(
                    conversation.id
                ),
            }
        )

    @staticmethod
    def _access_denied_response():
        return JsonResponse(
            {
                "status": "ERROR",
                "error": "You do not have access to this conversation.",
            },
            status=403,
        )

    @staticmethod
    def _serialize_conversation(
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
                ConversationDetailAPIView._serialize_message(
                    message
                )
                for message in conversation.messages.all()
            ],
        }

    @staticmethod
    def _serialize_message(
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
    guidance_service = QueryGuidanceService()

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
                    "status": "ERROR",
                    "error": "Invalid JSON request body.",
                },
                status=400,
            )

        question = payload.get("question")

        if not isinstance(question, str) or not question.strip():
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": "Question is required.",
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
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": str(exc),
                },
                status=500,
            )

        if not can_access_conversation_subject(
            request.user,
            conversation.subject,
        ):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": (
                        "You do not have access to "
                        "this conversation."
                    ),
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
            rag_service = RagService(
                enable_llm_reframing=True
            )

            result = rag_service.answer_question_with_sources(
                user=request.user,
                question=question,
                subject=conversation.subject,
                top_k=top_k,
                conversation_history=history,
            )


        except RagClarificationRequiredError:
            guidance = self.guidance_service.build(
                question=question.strip(),
                reason=QueryGuidanceService.CLARIFICATION,
                subject=conversation.subject,
                conversation_history=history,
            )

            return JsonResponse(
                {
                    "status": "CLARIFICATION",
                    "user_message_id": str(
                        user_message.id
                    ),
                    "guidance": {
                        "message": guidance.message,
                        "suggestions": list(
                            guidance.suggestions
                        ),
                        "reason": guidance.reason,
                    },
                }
            )
        except RagNoRelevantContextError:
            guidance = self.guidance_service.build(
                question=question.strip(),
                reason=(
                    QueryGuidanceService.NO_RELEVANT_CONTEXT
                ),
                subject=conversation.subject,
                conversation_history=history,
            )

            return JsonResponse(
                {
                    "status": "NO_RELEVANT_CONTEXT",
                    "user_message_id": str(
                        user_message.id
                    ),
                    "guidance": {
                        "message": guidance.message,
                        "suggestions": list(
                            guidance.suggestions
                        ),
                        "reason": guidance.reason,
                    },
                }
            )
        except RagServiceError as exc:
            return JsonResponse(
                {
                    "status": "ERROR",
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
                "status": "ANSWER",
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
            return None

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
        ):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": "top_k must be an integer.",
                },
                status=400,
            )

        if value <= 0:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": "top_k must be greater than zero.",
                },
                status=400,
            )

        if value > MAX_TOP_K:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": (
                        f"top_k cannot exceed {MAX_TOP_K}."
                    ),
                },
                status=400,
            )

        return value

    @staticmethod
    def _serialize_sources(chunks):
        sources = []

        for chunk in chunks:
            document_version = getattr(
                chunk,
                "document_version",
                None,
            )

            if document_version is None:
                continue

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
                    "page_number": getattr(
                        chunk,
                        "page_number",
                        None,
                    ),
                }
            )

        return sources

    @staticmethod
    def _serialize_message(
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