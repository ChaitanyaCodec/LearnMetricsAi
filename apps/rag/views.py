import json
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from apps.academics.models import Subject
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
from .services import RagService, RagServiceError


class RagAskAPIView(LoginRequiredMixin, View):
    """
    Stateless RAG question-answer endpoint.

    Existing endpoint retained for compatibility:
        POST /rag/ask/
    """

    def post(self, request):
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON payload."},
                status=400,
            )

        question = data.get("question")
        subject_id = data.get("subject_id")
        top_k = data.get("top_k")

        # Validate all primitive inputs before database access.
        if not isinstance(question, str) or not question.strip():
            return JsonResponse(
                {"error": "Question is required."},
                status=400,
            )

        if not isinstance(subject_id, int) or isinstance(subject_id, bool):
            return JsonResponse(
                {"error": "A valid subject_id is required."},
                status=400,
            )

        if top_k is not None:
            if not isinstance(top_k, int) or isinstance(top_k, bool):
                return JsonResponse(
                    {"error": "top_k must be an integer."},
                    status=400,
                )

        try:
            subject = Subject.objects.get(pk=subject_id)
        except Subject.DoesNotExist:
            return JsonResponse(
                {"error": "Subject not found."},
                status=404,
            )

        if not _can_access_subject(request.user, subject):
            return JsonResponse(
                {"error": "You are not authorized to access this subject."},
                status=403,
            )

        service = RagService()

        try:
            result = service.answer_question_with_sources(
                user=request.user,
                question=question,
                subject=subject,
                top_k=top_k,
            )
        except RagServiceError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=500,
            )

        return JsonResponse(
            {
                "answer": result.answer,
                "sources": self._serialize_sources(result.chunks),
            }
        )

    @staticmethod
    def _serialize_sources(chunks):
        """
        Compatibility wrapper for existing API tests and callers.

        Source serialization remains centralized in the module-level
        helper so conversation and stateless RAG APIs use the same
        deterministic citation format.
        """
        return _serialize_sources(chunks)


class ConversationListCreateAPIView(LoginRequiredMixin, View):
    """
    Conversation collection endpoint.

    GET:
        /rag/conversations/

    POST:
        /rag/conversations/
    """

    def get(self, request):
        service = ConversationService()

        try:
            conversations = service.list_conversations(
                user=request.user
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

        return JsonResponse(
            {
                "conversations": [
                    _serialize_conversation(conversation)
                    for conversation in conversations
                ]
            }
        )

    def post(self, request):
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON payload."},
                status=400,
            )

        subject_id = data.get("subject_id")
        title = data.get("title", "")

        try:
            subject_id = int(subject_id)
        except (TypeError, ValueError):
            return JsonResponse(
                {"error": "A valid subject_id is required."},
                status=400,
            )

        try:
            subject = Subject.objects.get(pk=subject_id)
        except Subject.DoesNotExist:
            return JsonResponse(
                {"error": "Subject not found."},
                status=404,
            )

        if not can_access_conversation_subject(
            request.user,
            subject,
        ):
            return JsonResponse(
                {"error": "You are not authorized to access this subject."},
                status=403,
            )

        service = ConversationService()

        try:
            conversation = service.create_conversation(
                user=request.user,
                subject=subject,
                title=title,
            )
        except ConversationValidationError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=500,
            )

        return JsonResponse(
            {
                "conversation": _serialize_conversation(conversation),
            },
            status=201,
        )


class ConversationDetailAPIView(LoginRequiredMixin, View):
    """
    Single conversation endpoint.

    GET:
        /rag/conversations/<conversation_id>/
    """

    def get(self, request, conversation_id):
        service = ConversationService()

        try:
            conversation = service.get_conversation(
                user=request.user,
                conversation_id=conversation_id,
            )
        except ConversationNotFoundError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

        return JsonResponse(
            {
                "conversation": _serialize_conversation(
                    conversation,
                    include_messages=True,
                )
            }
        )


class ConversationMessageAPIView(LoginRequiredMixin, View):
    """
    Persistent RAG conversation endpoint.

    POST:
        /rag/conversations/<conversation_id>/messages/
    """

    def post(self, request, conversation_id):
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON payload."},
                status=400,
            )

        question = data.get("question")

        if not isinstance(question, str) or not question.strip():
            return JsonResponse(
                {"error": "Question is required."},
                status=400,
            )

        conversation_service = ConversationService()

        try:
            conversation = conversation_service.get_conversation(
                user=request.user,
                conversation_id=conversation_id,
            )
        except ConversationNotFoundError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=404,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

        if not can_access_conversation_subject(
            request.user,
            conversation.subject,
        ):
            return JsonResponse(
                {"error": "You are not authorized to access this subject."},
                status=403,
            )

        top_k = data.get("top_k")

        if top_k is not None:
            if not isinstance(top_k, int) or isinstance(top_k, bool):
                return JsonResponse(
                    {"error": "top_k must be an integer."},
                    status=400,
                )

        # Load previous conversation history BEFORE saving the
        # current user message so the current question is not
        # duplicated inside the generation context.
        try:
            conversation_history = (
                conversation_service.get_conversation_history(
                    user=request.user,
                    conversation_id=conversation_id,
                )
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

        # Persist the student's question first.
        try:
            user_message = conversation_service.add_user_message(
                user=request.user,
                conversation_id=conversation_id,
                content=question,
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

        # Run the existing RAG pipeline with previous conversation
        # context.
        rag_service = RagService()

        try:
            result = rag_service.answer_question_with_sources(
                user=request.user,
                question=question,
                subject=conversation.subject,
                top_k=top_k,
                conversation_history=conversation_history,
            )
        except RagServiceError as exc:
            # The USER message intentionally remains persisted.
            return JsonResponse(
                {
                    "error": str(exc),
                    "message_id": str(user_message.id),
                },
                status=502,
            )

        sources = _serialize_sources(result.chunks)

        # Persist the generated answer and deterministic source metadata.
        try:
            assistant_message = (
                conversation_service.add_assistant_message(
                    user=request.user,
                    conversation_id=conversation_id,
                    content=result.answer,
                    sources=sources,
                )
            )
        except ConversationServiceError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=500,
            )

        return JsonResponse(
            {
                "user_message": _serialize_message(user_message),
                "assistant_message": _serialize_message(
                    assistant_message
                ),
                "answer": result.answer,
                "sources": sources,
            }
        )


def _can_access_subject(user, subject):
        """
        Centralizes subject authorization for RAG APIs.
        """

        if is_documents_admin(user):
            return True

        if teacher_can_upload_for_subject(user, subject):
            return True

        if student_can_access_subject(user, subject):
            return True

        return False


def _serialize_sources(chunks):
        """
        Convert retrieved DocumentChunk objects into deterministic
        citation metadata.

        No document content, files, or embeddings are exposed.
        """

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


def _serialize_conversation(
        conversation,
        *,
        include_messages=False,
    ):
        data = {
            "id": str(conversation.id),
            "subject_id": conversation.subject_id,
            "subject_name": conversation.subject.name,
            "title": conversation.title,
            "is_active": conversation.is_active,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }

        if include_messages:
            data["messages"] = [
                _serialize_message(message)
                for message in conversation.messages.all()
            ]

        return data


def _serialize_message(message):
        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "role": message.role,
            "content": message.content,
            "sequence": message.sequence,
            "metadata": message.metadata,
            "created_at": message.created_at.isoformat(),
        }