import re

from .constants import (
    MAX_CONSTRAINT_LENGTH,
    MAX_CONSTRAINTS,
    MAX_QUESTION_LENGTH,
    MAX_SUBJECT_LENGTH,
    MAX_TOPIC_LENGTH,
    ReframerIntent,
    ReframerOutputFormat,
)
from .llm import LLMReframer
from .models import PromptReframerResult


LLM_REFRAME_CONFIDENCE_THRESHOLD = 0.75


class PromptReframer:
    """
    Controlled prompt reframing pipeline.

    Stage 1:
        Deterministic interpretation.

    Stage 2:
        Optional LLM-assisted interpretation for low-confidence
        deterministic results.

    The LLM never answers the student's question. It only returns
    structured intent information.

    If the LLM layer is unavailable or fails, the deterministic
    result is returned unchanged.
    """

    _INTENT_PATTERNS = (
        (
            ReframerIntent.FLASHCARDS,
            (
                r"\bflash\s*cards?\b",
                r"\bflashcards?\b",
            ),
        ),
        (
            ReframerIntent.PRACTICE_QUESTIONS,
            (
                r"\bpractice questions?\b",
                r"\bpractice problems?\b",
                r"\bimportant questions?\b",
                r"\bexam questions?\b",
                r"\bquestions? (?:for|from|on)\b",
            ),
        ),
        (
            ReframerIntent.SUMMARY,
            (
                r"\bsummar(?:y|ize|ise)\b",
                r"\bshort notes?\b",
                r"\bbrief notes?\b",
                r"\bkey points?\b",
            ),
        ),
        (
            ReframerIntent.COMPARISON,
            (
                r"\bcompare\b",
                r"\bcomparison\b",
                r"\bdifference between\b",
                r"\bdifferentiate between\b",
                r"\bdistinguish between\b",
            ),
        ),
        (
            ReframerIntent.EXPLANATION,
            (
                r"\bexplain\b",
                r"\bexplanation\b",
                r"\bhow does\b",
                r"\bhow do\b",
                r"\bwhy does\b",
                r"\bwhy do\b",
            ),
        ),
        (
            ReframerIntent.EXAM_PREPARATION,
            (
                r"\bimportant topics?\b",
                r"\bimportant concepts?\b",
                r"\bexam preparation\b",
                r"\bfor my exam\b",
                r"\bwhat should i study\b",
                r"\bwhat to study\b",
                r"\bhigh[- ]?priority topics?\b",
                r"\bkey topics?\b",
            ),
        ),
    )

    _NUMBER_PATTERN = re.compile(
        r"\b(\d{1,3})"
        r"(?:\s+\w+){0,3}\s+"
        r"(questions?|cards?|flashcards?|points?|topics?|examples?)\b",
        re.IGNORECASE,
    )

    def __init__(self, llm_reframer=None):
        """
        Initialize the prompt reframer.

        llm_reframer is dependency-injected when supplied.

        When it is not supplied, the existing LearnMetrics AI
        provider factory is used lazily only when a low-confidence
        question requires LLM-assisted reframing.

        Expected interface:

            llm_reframer.reframe(
                question=...,
                subject=...,
                fallback=...
            )

        The deterministic reframer remains fully functional even
        when no LLM provider is configured.
        """
        self.llm_reframer = llm_reframer

    def reframe(
        self,
        question: str,
        subject: str | None = None,
    ) -> PromptReframerResult:
        normalized_question = self._validate_question(question)
        normalized_subject = self._normalize_subject(subject)

        deterministic_result = self._build_deterministic_result(
            normalized_question,
            normalized_subject,
        )

        if (
            self.llm_reframer is None
            or deterministic_result.confidence
            >= LLM_REFRAME_CONFIDENCE_THRESHOLD
        ):
            return deterministic_result

        return self._try_llm_reframing(
            deterministic_result=deterministic_result,
            question=normalized_question,
            subject=normalized_subject,
        )

    def _build_deterministic_result(
        self,
        question: str,
        subject: str | None,
    ) -> PromptReframerResult:
        intent, confidence = self._detect_intent(question)

        topic = self._extract_topic(
            question,
            subject,
        )

        output_format = self._detect_output_format(intent)

        constraints = self._extract_constraints(
            question
        )

        clarification_needed = (
            intent == ReframerIntent.UNKNOWN
        )

        return PromptReframerResult(
            original_question=question,
            intent=intent,
            topic=topic,
            output_format=output_format,
            constraints=tuple(constraints),
            clarification_needed=clarification_needed,
            confidence=confidence,
        )

    def _try_llm_reframing(
        self,
        *,
        deterministic_result: PromptReframerResult,
        question: str,
        subject: str | None,
    ) -> PromptReframerResult:
        """
        Ask the LLM reframer to improve a low-confidence
        deterministic interpretation.

        The existing provider factory is used here rather than
        creating or duplicating provider configuration.

        Any failure returns the deterministic result.

        The deterministic result therefore remains the safety
        fallback and the LLM is never a single point of failure.
        """
        try:
            if self.llm_reframer is None:
                from ..generation.providers.factory import (
                    get_llm_provider,
                )

                provider_manager = get_llm_provider()

                self.llm_reframer = LLMReframer(
                    provider_manager=provider_manager
                )

            result = self.llm_reframer.reframe(
                question=question,
                subject=subject,
                fallback=deterministic_result,
            )

            if not isinstance(
                result,
                PromptReframerResult,
            ):
                return deterministic_result

            if result.original_question != question:
                return deterministic_result

            return result

        except Exception:
            return deterministic_result

    @staticmethod
    def _validate_question(question: str) -> str:
        if not isinstance(question, str):
            raise ValueError(
                "question must be a string."
            )

        question = question.strip()

        if not question:
            raise ValueError(
                "question cannot be empty."
            )

        if len(question) > MAX_QUESTION_LENGTH:
            raise ValueError(
                "question cannot exceed "
                f"{MAX_QUESTION_LENGTH} characters."
            )

        return question

    @staticmethod
    def _normalize_subject(
        subject: str | None,
    ) -> str | None:
        if subject is None:
            return None

        if not isinstance(subject, str):
            raise ValueError(
                "subject must be a string or None."
            )

        subject = " ".join(subject.split())

        if not subject:
            return None

        return subject[:MAX_SUBJECT_LENGTH]

    def _detect_intent(
        self,
        question: str,
    ) -> tuple[ReframerIntent, float]:
        lowered = question.lower()

        matches = []

        for intent, patterns in self._INTENT_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, lowered):
                    matches.append(intent)
                    break

        if not matches:
            return (
                ReframerIntent.GENERAL_QA,
                0.55,
            )

        unique_matches = list(dict.fromkeys(matches))

        if len(unique_matches) == 1:
            return (
                unique_matches[0],
                0.90,
            )

        return (
            ReframerIntent.UNKNOWN,
            0.35,
        )

    def _extract_topic(
        self,
        question: str,
        subject: str | None,
    ) -> str | None:
        """
        Extract only explicit topic-like wording.

        The selected subject is returned when no narrower topic is
        explicitly identifiable. The service never invents a topic.
        """

        patterns = (
            r"\babout\s+(.+?)(?:\?|$)",
            r"\bon\s+(.+?)(?:\?|$)",
            r"\bof\s+(.+?)(?:\?|$)",
            r"\bfrom\s+(.+?)(?:\?|$)",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                question,
                flags=re.IGNORECASE,
            )

            if match:
                candidate = self._clean_topic(
                    match.group(1)
                )

                if candidate:
                    return candidate

        return subject

    @staticmethod
    def _clean_topic(value: str) -> str | None:
        value = value.strip()

        value = re.sub(
            r"\b(?:please|give me|tell me|show me)\b",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"\b(?:important|key|main|major)\b",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = " ".join(value.split())
        value = value.strip(" .,:;!?")

        if not value:
            return None

        return value[:MAX_TOPIC_LENGTH]

    @staticmethod
    def _detect_output_format(
        intent: ReframerIntent,
    ) -> ReframerOutputFormat:
        mapping = {
            ReframerIntent.FLASHCARDS:
                ReframerOutputFormat.FLASHCARDS,

            ReframerIntent.SUMMARY:
                ReframerOutputFormat.SUMMARY,

            ReframerIntent.COMPARISON:
                ReframerOutputFormat.COMPARISON_TABLE,

            ReframerIntent.EXPLANATION:
                ReframerOutputFormat.EXPLANATION,

            ReframerIntent.PRACTICE_QUESTIONS:
                ReframerOutputFormat.PRACTICE_SET,

            ReframerIntent.EXAM_PREPARATION:
                ReframerOutputFormat.LIST,

            ReframerIntent.GENERAL_QA:
                ReframerOutputFormat.DEFAULT,

            ReframerIntent.UNKNOWN:
                ReframerOutputFormat.DEFAULT,
        }

        return mapping[intent]

    def _extract_constraints(
        self,
        question: str,
    ) -> list[str]:
        constraints = []

        number_match = self._NUMBER_PATTERN.search(
            question
        )

        if number_match:
            count = number_match.group(1)
            item_type = number_match.group(2).lower()

            if item_type in {
                "card",
                "cards",
                "flashcard",
                "flashcards",
            }:
                normalized_type = "flashcards"

            elif item_type in {
                "question",
                "questions",
            }:
                normalized_type = "questions"

            elif item_type in {
                "point",
                "points",
            }:
                normalized_type = "points"

            elif item_type in {
                "topic",
                "topics",
            }:
                normalized_type = "topics"

            elif item_type in {
                "example",
                "examples",
            }:
                normalized_type = "examples"

            else:
                normalized_type = item_type

            constraints.append(
                f"{count} {normalized_type}"
            )

        lowered = question.lower()

        if (
            "short answer" in lowered
            or "short answers" in lowered
        ):
            constraints.append("short answers")

        if (
            "detailed" in lowered
            or "in detail" in lowered
            or "in-depth" in lowered
            or "in depth" in lowered
        ):
            constraints.append("detailed explanation")

        if "beginner" in lowered:
            constraints.append("beginner level")

        if "easy" in lowered:
            constraints.append("easy difficulty")

        if "medium" in lowered:
            constraints.append("medium difficulty")

        if (
            "hard" in lowered
            or "difficult" in lowered
        ):
            constraints.append("difficult level")

        if (
            "exam-focused" in lowered
            or "exam focused" in lowered
            or "exam oriented" in lowered
            or "exam-oriented" in lowered
        ):
            constraints.append("exam-focused")

        cleaned = []

        for constraint in constraints:
            constraint = constraint[
                :MAX_CONSTRAINT_LENGTH
            ]

            if constraint not in cleaned:
                cleaned.append(constraint)

            if len(cleaned) >= MAX_CONSTRAINTS:
                break

        return cleaned