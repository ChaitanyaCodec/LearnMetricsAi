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
    Handles conversation and chat-message persistence.

    This service deliberately does not perform embedding, retrieval,
    or answer generation. Those responsibilities belong to RagService.
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
            .filter(user=user, is_active=True)
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
                "Conversation was not found."
            ) from exc

    def get_conversation_history(
        self,
        *,
        user,
        conversation_id,
        limit=None,
    ):
        """
        Return the latest messages from a conversation in
        chronological order.

        Conversation ownership is enforced through get_conversation().
        The limit applies to the number of most recent messages.
        """

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

        conversation = self.get_conversation(
            user=user,
            conversation_id=conversation_id,
        )

        with transaction.atomic():
            last_message = (
                ChatMessage.objects
                .select_for_update()
                .filter(conversation=conversation)
                .order_by("-sequence")
                .first()
            )

            next_sequence = (
                last_message.sequence + 1
                if last_message is not None
                else 1
            )

            message = ChatMessage.objects.create(
                conversation=conversation,
                role=role,
                content=content.strip(),
                sequence=next_sequence,
                metadata=dict(metadata or {}),
            )

            conversation.save(update_fields=["updated_at"])

        return message

    @staticmethod
    def _resolve_history_limit(limit):
        if limit is None:
            limit = getattr(
                settings,
                "RAG_CONVERSATION_HISTORY_LIMIT",
                DEFAULT_HISTORY_LIMIT,
            )

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ConversationValidationError(
                "Conversation history limit must be an integer."
            )

        if limit <= 0:
            raise ConversationValidationError(
                "Conversation history limit must be greater than zero."
            )

        if limit > MAX_HISTORY_LIMIT:
            raise ConversationValidationError(
                f"Conversation history limit cannot exceed "
                f"{MAX_HISTORY_LIMIT}."
            )

        return limit

    @staticmethod
    def _validate_user(user):
        if (
            user is None
            or not getattr(user, "is_authenticated", False)
            or not getattr(user, "is_active", False)
        ):
            raise ConversationValidationError(
                "An authenticated active user is required."
            )

    @staticmethod
    def _validate_subject(subject):
        if not isinstance(subject, Subject):
            raise ConversationValidationError(
                "A valid subject is required."
            )

    @staticmethod
    def _validate_title(title):
        if not isinstance(title, str):
            raise ConversationValidationError(
                "Conversation title must be a string."
            )

    @staticmethod
    def _validate_content(content):
        if not isinstance(content, str):
            raise ConversationValidationError(
                "Message content must be a string."
            )

        if not content.strip():
            raise ConversationValidationError(
                "Message content cannot be empty."
            )