from dataclasses import dataclass
from typing import Tuple

from .constants import (
    ReframerIntent,
    ReframerOutputFormat,
)


@dataclass(frozen=True)
class PromptReframerResult:
    """
    Structured interpretation of a student's question.

    This object describes the request only. It does not contain
    generated academic content.
    """

    original_question: str
    intent: ReframerIntent
    topic: str | None
    output_format: ReframerOutputFormat
    constraints: Tuple[str, ...]
    clarification_needed: bool
    confidence: float

    def __post_init__(self):
        if not self.original_question.strip():
            raise ValueError("original_question cannot be empty.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0."
            )

        if self.clarification_needed and (
            self.intent != ReframerIntent.UNKNOWN
        ):
            raise ValueError(
                "Clarification is only expected for UNKNOWN intent."
            )