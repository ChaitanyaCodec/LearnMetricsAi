import json

from ..generation.exceptions import GenerationError
from .constants import (
    MAX_CONSTRAINT_LENGTH,
    MAX_CONSTRAINTS,
    MAX_QUESTION_LENGTH,
    MAX_SUBJECT_LENGTH,
    MAX_TOPIC_LENGTH,
    ReframerIntent,
    ReframerOutputFormat,
)
from .models import PromptReframerResult
from .prompts import build_reframing_prompt


class LLMReframer:
    """
    Controlled LLM-assisted prompt reframer.

    The LLM is used only to classify and structure the student's
    request. It never generates the academic answer.

    A deterministic fallback result must be supplied by the caller.
    """

    def __init__(self, provider_manager):
        if provider_manager is None:
            raise ValueError("provider_manager is required.")

        self.provider_manager = provider_manager

    def reframe(
        self,
        *,
        question: str,
        subject: str | None = None,
        fallback: PromptReframerResult | None = None,
    ) -> PromptReframerResult:
        normalized_question = self._validate_question(question)
        normalized_subject = self._validate_subject(subject)

        try:
            prompt = build_reframing_prompt(
                question=normalized_question,
                subject=normalized_subject,
            )

            raw_response = self.provider_manager.generate(prompt)

            result = self._parse_response(
                raw_response,
                original_question=normalized_question,
            )

            self._validate_result(
                result,
                subject=normalized_subject,
            )

            return result

        except (GenerationError, ValueError, TypeError, json.JSONDecodeError):
            if fallback is not None:
                return fallback

            raise

        except Exception:
            if fallback is not None:
                return fallback

            raise

    @staticmethod
    def _validate_question(question: str) -> str:
        if not isinstance(question, str):
            raise ValueError("question must be a string.")

        normalized = question.strip()

        if not normalized:
            raise ValueError("question cannot be empty.")

        if len(normalized) > MAX_QUESTION_LENGTH:
            raise ValueError(
                f"question cannot exceed {MAX_QUESTION_LENGTH} characters."
            )

        return normalized

    @staticmethod
    def _validate_subject(subject: str | None) -> str | None:
        if subject is None:
            return None

        if not isinstance(subject, str):
            raise ValueError("subject must be a string.")

        normalized = subject.strip()

        if not normalized:
            return None

        if len(normalized) > MAX_SUBJECT_LENGTH:
            raise ValueError(
                f"subject cannot exceed {MAX_SUBJECT_LENGTH} characters."
            )

        return normalized

    @classmethod
    def _parse_response(
        cls,
        raw_response: str,
        *,
        original_question: str,
    ) -> PromptReframerResult:
        if not isinstance(raw_response, str):
            raise ValueError("LLM response must be a string.")

        response = raw_response.strip()

        if not response:
            raise ValueError("LLM response cannot be empty.")

        # We deliberately require plain JSON rather than silently
        # extracting JSON from markdown or arbitrary text.
        payload = json.loads(response)

        if not isinstance(payload, dict):
            raise ValueError("LLM response must be a JSON object.")

        required_fields = {
            "original_question",
            "intent",
            "topic",
            "output_format",
            "constraints",
            "clarification_needed",
            "confidence",
        }

        if not required_fields.issubset(payload):
            raise ValueError("LLM response is missing required fields.")

        if payload["original_question"] != original_question:
            raise ValueError(
                "LLM modified the original question."
            )

        try:
            intent = ReframerIntent(payload["intent"])
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid reframer intent.") from exc

        try:
            output_format = ReframerOutputFormat(
                payload["output_format"]
            )
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid reframer output format.") from exc

        topic = payload["topic"]

        if topic is not None:
            if not isinstance(topic, str):
                raise ValueError("topic must be a string or null.")

            topic = topic.strip()

            if len(topic) > MAX_TOPIC_LENGTH:
                raise ValueError(
                    f"topic cannot exceed {MAX_TOPIC_LENGTH} characters."
                )

            if not topic:
                topic = None

        constraints = payload["constraints"]

        if not isinstance(constraints, list):
            raise ValueError("constraints must be a list.")

        if len(constraints) > MAX_CONSTRAINTS:
            raise ValueError(
                f"constraints cannot contain more than "
                f"{MAX_CONSTRAINTS} items."
            )

        normalized_constraints = []

        for constraint in constraints:
            if not isinstance(constraint, str):
                raise ValueError(
                    "Every constraint must be a string."
                )

            normalized = constraint.strip()

            if not normalized:
                raise ValueError(
                    "Constraints cannot contain empty strings."
                )

            if len(normalized) > MAX_CONSTRAINT_LENGTH:
                raise ValueError(
                    "A constraint exceeds the maximum allowed length."
                )

            normalized_constraints.append(normalized)

        clarification_needed = payload["clarification_needed"]

        if not isinstance(clarification_needed, bool):
            raise ValueError(
                "clarification_needed must be boolean."
            )

        confidence = payload["confidence"]

        if isinstance(confidence, bool):
            raise ValueError("confidence must be numeric.")

        if not isinstance(confidence, (int, float)):
            raise ValueError("confidence must be numeric.")

        confidence = float(confidence)

        result = PromptReframerResult(
            original_question=original_question,
            intent=intent,
            topic=topic,
            output_format=output_format,
            constraints=tuple(normalized_constraints),
            clarification_needed=clarification_needed,
            confidence=confidence,
        )

        return result

    @staticmethod
    def _validate_result(
        result: PromptReframerResult,
        *,
        subject: str | None,
    ) -> None:
        if result.clarification_needed:
            if result.intent != ReframerIntent.UNKNOWN:
                raise ValueError(
                    "Clarification requires UNKNOWN intent."
                )

        if result.intent == ReframerIntent.UNKNOWN:
            if not result.clarification_needed:
                raise ValueError(
                    "UNKNOWN intent requires clarification."
                )
