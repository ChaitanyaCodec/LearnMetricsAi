
from .config import (
    MAX_ALLOWED_CONTEXT_CHARACTERS,
    MAX_ALLOWED_CONTEXT_CHUNKS,
    get_max_context_characters,
    get_max_context_chunks,
)
from .providers.factory import get_llm_provider
from .exceptions import GenerationError


class AnswerGenerationService:
    """
    Builds a grounded generation prompt from retrieved
    document chunks, conversation history, and optional
    prompt-reframing metadata.

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
        reframing_result=None,
    ):
        self._validate_question(question)

        if chunks is None:
            raise GenerationError(
                "Retrieved chunks are required."
            )

        chunks = list(chunks)

        max_chunks = self._resolve_max_context_chunks()

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
            reframing_result=reframing_result,
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
    def _resolve_max_context_chunks():
        value = get_max_context_chunks()

        if isinstance(value, bool) or not isinstance(value, int):
            raise GenerationError(
                "Maximum context chunks must be an integer."
            )

        if value <= 0:
            raise GenerationError(
                "Maximum context chunks must be greater than zero."
            )

        if value > MAX_ALLOWED_CONTEXT_CHUNKS:
            raise GenerationError(
                f"Maximum context chunks cannot exceed "
                f"{MAX_ALLOWED_CONTEXT_CHUNKS}."
            )

        return value

    @staticmethod
    def _resolve_max_context_characters():
        value = get_max_context_characters()

        if isinstance(value, bool) or not isinstance(value, int):
            raise GenerationError(
                "Maximum context characters must be an integer."
            )

        if value <= 0:
            raise GenerationError(
                "Maximum context characters must be greater than zero."
            )

        if value > MAX_ALLOWED_CONTEXT_CHARACTERS:
            raise GenerationError(
                f"Maximum context characters cannot exceed "
                f"{MAX_ALLOWED_CONTEXT_CHARACTERS}."
            )

        return value

    @classmethod
    def _build_context(cls, chunks):
        max_characters = cls._resolve_max_context_characters()

        parts = []
        total_characters = 0
        source_number = 0

        for chunk in chunks:
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

            if not content:
                continue

            source_number += 1

            parts.append(
                f"[Source {source_number}]\n{content}"
            )

            total_characters += len(content)

        return "\n\n".join(parts)

    @staticmethod
    def _build_history(conversation_history):
        """
        Convert conversation messages into prompt text.

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
    def _build_reframing_section(reframing_result):
        """
        Build a controlled prompt section from the structured
        prompt-reframing result.

        Only explicitly approved metadata is included.
        The original question itself is kept separately in
        the CURRENT QUESTION section.
        """

        if reframing_result is None:
            return "No prompt-reframing metadata available."

        intent = getattr(
            reframing_result,
            "intent",
            None,
        )

        topic = getattr(
            reframing_result,
            "topic",
            None,
        )

        output_format = getattr(
            reframing_result,
            "output_format",
            None,
        )

        constraints = getattr(
            reframing_result,
            "constraints",
            (),
        )

        intent = getattr(
            intent,
            "value",
            intent,
        )

        output_format = getattr(
            output_format,
            "value",
            output_format,
        )

        lines = [
            "REFRAMED REQUEST:",
            f"Intent: {intent or 'UNKNOWN'}",
            f"Topic: {topic or 'Not specified'}",
            f"Output format: "
            f"{output_format or 'DEFAULT'}",
        ]

        normalized_constraints = []

        if constraints is not None:
            try:
                constraints = list(constraints)
            except TypeError:
                constraints = []

        for constraint in constraints:
            if isinstance(constraint, str):
                constraint = constraint.strip()

                if (
                    constraint
                    and constraint
                    not in normalized_constraints
                ):
                    normalized_constraints.append(
                        constraint
                    )

        if normalized_constraints:
            lines.append("Constraints:")

            for constraint in normalized_constraints:
                lines.append(f"- {constraint}")
        else:
            lines.append("Constraints: None specified")

        return "\n".join(lines)

    @classmethod
    def _build_prompt(
        cls,
        *,
        question,
        context,
        history="",
        reframing_result=None,
    ):
        history_section = (
            history
            if history
            else "No previous conversation."
        )

        reframing_section = (
            cls._build_reframing_section(
                reframing_result
            )
        )

        return (
            "You are an educational assistant for LearnMetrics AI.\n"
            "Answer the student's question using only the provided "
            "document context.\n"
            "Use conversation history only to understand references "
            "and follow-up questions.\n"
            "The retrieved document context is the authoritative "
            "source of factual information.\n"
            "Prompt-reframing metadata describes the student's "
            "requested intent and format. Use it to shape the "
            "response, but do not treat it as factual academic "
            "content.\n"
            "If the document context does not contain enough "
            "information, clearly say that the information is not "
            "available in the provided documents.\n"
            "Do not invent facts.\n\n"
            f"CONVERSATION HISTORY:\n"
            f"{history_section}\n\n"
            f"{reframing_section}\n\n"
            f"RETRIEVED DOCUMENT CONTEXT:\n"
            f"{context}\n\n"
            f"CURRENT QUESTION:\n"
            f"{question.strip()}\n\n"
            "ANSWER:"
        )