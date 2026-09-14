from .config import (
    get_max_context_characters,
    get_max_context_chunks,
)
from .exceptions import GenerationError
from .providers.factory import get_llm_provider


class AnswerGenerationService:
    """
    Builds a grounded generation prompt from retrieved
    document chunks and conversation history.

    Provider selection and fallback are handled by the
    provider factory and manager.
    """

    def __init__(self, provider=None):
        self.provider = (
            provider
            if provider is not None
            else get_llm_provider()
        )

    def generate(
        self,
        *,
        question,
        chunks,
        conversation_history=None,
    ):
        self._validate_question(question)

        if chunks is None:
            raise GenerationError(
                "Retrieved chunks are required."
            )

        chunks = list(chunks)

        max_chunks = get_max_context_chunks()

        if len(chunks) > max_chunks:
            chunks = chunks[:max_chunks]

        context = self._build_context(chunks)

        if not context:
            raise GenerationError(
                "No usable context was retrieved."
            )

        history = self._build_history(
            conversation_history
        )

        prompt = self._build_prompt(
            question=question,
            context=context,
            history=history,
        )

        try:
            return self.provider.generate(prompt)
        except GenerationError:
            raise
        except Exception as exc:
            raise GenerationError(
                "Failed to generate an answer."
            ) from exc

    @staticmethod
    def _validate_question(question):
        if not isinstance(question, str):
            raise GenerationError(
                "Question must be a string."
            )

        if not question.strip():
            raise GenerationError(
                "Question cannot be empty."
            )

    @staticmethod
    def _build_context(chunks):
        max_characters = get_max_context_characters()

        parts = []
        total_characters = 0

        for index, chunk in enumerate(chunks, start=1):
            content = getattr(chunk, "content", None)

            if not isinstance(content, str):
                continue

            content = content.strip()

            if not content:
                continue

            remaining = max_characters - total_characters

            if remaining <= 0:
                break

            content = content[:remaining]

            parts.append(
                f"[Source {index}]\n{content}"
            )

            total_characters += len(content)

        return "\n\n".join(parts)

    @staticmethod
    def _build_history(conversation_history):
        """
        Convert conversation messages into bounded prompt text.

        The supplied history is expected to already be ordered
        chronologically by ConversationService.
        """

        if conversation_history is None:
            return ""

        try:
            messages = list(conversation_history)
        except TypeError as exc:
            raise GenerationError(
                "Conversation history must be iterable."
            ) from exc

        parts = []

        for message in messages:
            role = getattr(message, "role", None)
            content = getattr(message, "content", None)

            if not isinstance(content, str):
                continue

            content = content.strip()

            if not content:
                continue

            if role == "user":
                label = "User"
            elif role == "assistant":
                label = "Assistant"
            else:
                continue

            parts.append(
                f"{label}: {content}"
            )

        return "\n".join(parts)

    @staticmethod
    def _build_prompt(
        *,
        question,
        context,
        history="",
    ):
        history_section = (
            history
            if history
            else "No previous conversation."
        )

        return (
            "You are an educational assistant for LearnMetrics AI.\n"
            "Answer the student's question using only the provided "
            "document context.\n"
            "Use conversation history only to understand references "
            "and follow-up questions.\n"
            "The retrieved document context is the authoritative "
            "source of factual information.\n"
            "If the document context does not contain enough "
            "information, clearly say that the information is not "
            "available in the provided documents.\n"
            "Do not invent facts.\n\n"
            f"CONVERSATION HISTORY:\n"
            f"{history_section}\n\n"
            f"RETRIEVED DOCUMENT CONTEXT:\n"
            f"{context}\n\n"
            f"CURRENT QUESTION:\n"
            f"{question.strip()}\n\n"
            "ANSWER:"
        )