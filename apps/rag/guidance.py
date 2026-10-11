from dataclasses import dataclass


@dataclass(frozen=True)
class QueryGuidance:
    """
    Structured guidance returned when the RAG pipeline cannot
    confidently answer a student's question from the available
    study material.
    """

    message: str
    suggestions: tuple[str, ...]
    reason: str


class QueryGuidanceService:
    """
    Builds deterministic, student-friendly guidance for questions
    that cannot currently be answered from retrieved context.

    This service deliberately does not call an LLM. Suggestions are
    based on the available subject and conversation context so that
    the guidance remains predictable and safe.
    """

    NO_RELEVANT_CONTEXT = "NO_RELEVANT_CONTEXT"
    CLARIFICATION = "CLARIFICATION"

    DEFAULT_SUGGESTIONS = (
        "List the important topics from the uploaded material.",
        "What are the key concepts I should study?",
        "Which topics are important for my exam?",
    )

    def build(
        self,
        *,
        question,
        reason=NO_RELEVANT_CONTEXT,
        subject=None,
        conversation_history=None,
    ):
        normalized_question = self._normalize_question(question)

        if reason == self.CLARIFICATION:
            return self._build_clarification_guidance(
                question=normalized_question,
                subject=subject,
                conversation_history=conversation_history,
            )

        return self._build_no_context_guidance(
            question=normalized_question,
            subject=subject,
            conversation_history=conversation_history,
        )

    def _build_no_context_guidance(
        self,
        *,
        question,
        subject=None,
        conversation_history=None,
    ):
        subject_name = self._subject_name(subject)

        if subject_name:
            message = (
                "I couldn't identify a specific topic in the "
                f"uploaded {subject_name} study material that "
                "matches your question. Try asking about a topic, "
                "chapter, or concept from the material."
            )

            suggestions = (
                f"List the important topics from {subject_name}.",
                f"What are the key concepts in {subject_name}?",
                f"Which {subject_name} topics should I study for my exam?",
            )
        else:
            message = (
                "I couldn't identify a specific topic or chapter "
                "from the uploaded study material. Try asking about "
                "a topic, chapter, or concept from the material."
            )

            suggestions = self.DEFAULT_SUGGESTIONS

        return QueryGuidance(
            message=message,
            suggestions=self._deduplicate_suggestions(
                suggestions
            ),
            reason=self.NO_RELEVANT_CONTEXT,
        )

    def _build_clarification_guidance(
        self,
        *,
        question,
        subject=None,
        conversation_history=None,
    ):
        subject_name = self._subject_name(subject)

        if subject_name:
            message = (
                f"Could you make your question a little more "
                f"specific about {subject_name}? For example, "
                "mention the topic, chapter, or concept you want "
                "to study."
            )

            suggestions = (
                f"List the important topics from {subject_name}.",
                f"Explain the key concepts in {subject_name}.",
                f"What are the important topics in the current chapter?",
            )
        else:
            message = (
                "Could you make your question a little more "
                "specific? Mention the topic, chapter, or concept "
                "you want to study."
            )

            suggestions = (
                "List the important topics from the uploaded material.",
                "What are the key concepts in the current chapter?",
                "Explain an important topic from the uploaded material.",
            )

        return QueryGuidance(
            message=message,
            suggestions=self._deduplicate_suggestions(
                suggestions
            ),
            reason=self.CLARIFICATION,
        )

    @staticmethod
    def _normalize_question(question):
        if not isinstance(question, str):
            return ""

        return question.strip()

    @staticmethod
    def _subject_name(subject):
        if subject is None:
            return ""

        if isinstance(subject, str):
            return subject.strip()

        name = getattr(subject, "name", "")
        if not isinstance(name, str):
            return ""

        return name.strip()

    @staticmethod
    def _deduplicate_suggestions(suggestions):
        seen = set()
        result = []

        for suggestion in suggestions:
            if not isinstance(suggestion, str):
                continue

            suggestion = suggestion.strip()

            if not suggestion:
                continue

            normalized = suggestion.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(suggestion)

        return tuple(result)