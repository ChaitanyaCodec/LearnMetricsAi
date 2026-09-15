from django.conf import settings
from django.db import transaction

from apps.academics.models import Subject
from apps.rag.models import ChatMessage, Conversation

from .exceptions import (
    ConversationNotFoundError,
    ConversationServiceError,
    ConversationValidationError,
)


DEFAULT_HISTORY_LIMIT = 10
MAX_HISTORY_LIMIT = 50


class ConversationService:
    """
    Service layer for persistent RAG conversations.

    Conversation ownership and message sequencing are enforced here
    so callers cannot accidentally access or mutate another user's
    conversation.
    """

    def create_conversation(self, *, user, subject, title=""):
        self._validate_user(user)
        self._validate_subject(subject)
        self._validate_title(title)

        try:
            return Conversation.objects.create(
                user=user,
                subject=subject,
                title=title.strip(),
            )
        except Exception as exc:
            raise ConversationServiceError(
                "Failed to create conversation."
            ) from exc

    def list_conversations(self, *, user):
        self._validate_user(user)

        return (
            Conversation.objects
            .filter(
                user=user,
                is_active=True,
            )
            .select_related("subject")
            .order_by("-updated_at")
        )

    def get_conversation(self, *, user, conversation_id):
        self._validate_user(user)

        try:
            return (
                Conversation.objects
                .select_related("subject")
                .prefetch_related("messages")
                .get(
                    id=conversation_id,
                    user=user,
                    is_active=True,
                )
            )
        except Conversation.DoesNotExist as exc:
            raise ConversationNotFoundError(
                "Conversation not found."
            ) from exc

    def get_conversation_history(
        self,
        *,
        user,
        conversation_id,
        limit=None,
    ):
        self._validate_user(user)

        conversation = self.get_conversation(
            user=user,
            conversation_id=conversation_id,
        )

        limit = self._resolve_history_limit(limit)

        messages = list(
            ChatMessage.objects
            .filter(conversation=conversation)
            .order_by("-sequence")[:limit]
        )

        messages.reverse()

        return messages

    def add_user_message(
        self,
        *,
        user,
        conversation_id,
        content,
        metadata=None,
    ):
        return self._add_message(
            user=user,
            conversation_id=conversation_id,
            role=ChatMessage.Role.USER,
            content=content,
            metadata=metadata,
        )

    def add_assistant_message(
        self,
        *,
        user,
        conversation_id,
        content,
        sources=None,
        metadata=None,
    ):
        metadata = dict(metadata or {})

        if sources is not None:
            metadata["sources"] = list(sources)

        return self._add_message(
            user=user,
            conversation_id=conversation_id,
            role=ChatMessage.Role.ASSISTANT,
            content=content,
            metadata=metadata,
        )

    def _add_message(
        self,
        *,
        user,
        conversation_id,
        role,
        content,
        metadata=None,
    ):
        self._validate_user(user)
        self._validate_content(content)

        metadata = dict(metadata or {})

        with transaction.atomic():
            try:
                # Lock the parent conversation row so concurrent
                # message writers for the same conversation are
                # serialized before calculating the next sequence.
                conversation = (
                    Conversation.objects
                    .select_for_update()
                    .select_related("subject")
                    .get(
                        id=conversation_id,
                        user=user,
                        is_active=True,
                    )
                )
            except Conversation.DoesNotExist as exc:
                raise ConversationNotFoundError(
                    "Conversation not found."
                ) from exc

            last_message = (
                ChatMessage.objects
                .filter(conversation=conversation)
                .order_by("-sequence")
                .first()
            )

            next_sequence = (
                last_message.sequence + 1
                if last_message is not None
                else 1
            )

            try:
                message = ChatMessage.objects.create(
                    conversation=conversation,
                    role=role,
                    content=content.strip(),
                    sequence=next_sequence,
                    metadata=metadata,
                )

                conversation.save(
                    update_fields=["updated_at"]
                )

            except Exception as exc:
                raise ConversationServiceError(
                    "Failed to create conversation message."
                ) from exc

        return message

    def _resolve_history_limit(self, limit):
        if limit is None:
            limit = getattr(
                settings,
                "RAG_CONVERSATION_HISTORY_LIMIT",
                DEFAULT_HISTORY_LIMIT,
            )

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ConversationValidationError(
                "History limit must be an integer."
            )

        if limit <= 0:
            raise ConversationValidationError(
                "History limit must be greater than zero."
            )

        if limit > MAX_HISTORY_LIMIT:
            raise ConversationValidationError(
                f"History limit cannot exceed {MAX_HISTORY_LIMIT}."
            )

        return limit

    def _validate_user(self, user):
        if not getattr(user, "is_authenticated", False):
            raise ConversationValidationError(
                "Authenticated user is required."
            )

        if not getattr(user, "is_active", False):
            raise ConversationValidationError(
                "Active user is required."
            )

    def _validate_subject(self, subject):
        if not isinstance(subject, Subject):
            raise ConversationValidationError(
                "A valid subject is required."
            )

    def _validate_title(self, title):
        if not isinstance(title, str):
            raise ConversationValidationError(
                "Conversation title must be a string."
            )

    def _validate_content(self, content):
        if not isinstance(content, str):
            raise ConversationValidationError(
                "Message content must be a string."
            )

        if not content.strip():
            raise ConversationValidationError(
                "Message content cannot be empty."
            )