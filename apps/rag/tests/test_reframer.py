import json
from unittest import TestCase
from unittest.mock import MagicMock

from apps.rag.reframing.constants import (
    ReframerIntent,
    ReframerOutputFormat,
)
from apps.rag.reframing.models import PromptReframerResult
from apps.rag.reframing.service import (
    LLM_REFRAME_CONFIDENCE_THRESHOLD,
    PromptReframer,
)


class PromptReframerTests(TestCase):

    def setUp(self):
        self.reframer = PromptReframer()

    def test_detects_exam_preparation(self):
        result = self.reframer.reframe(
            "List the important topics for my exam.",
            subject="Big Data Analytics",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.EXAM_PREPARATION,
        )
        self.assertEqual(
            result.output_format,
            ReframerOutputFormat.LIST,
        )
        self.assertFalse(
            result.clarification_needed
        )

    def test_detects_flashcards(self):
        result = self.reframer.reframe(
            "Make flashcards for operating system.",
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.FLASHCARDS,
        )
        self.assertEqual(
            result.output_format,
            ReframerOutputFormat.FLASHCARDS,
        )

    def test_detects_summary(self):
        result = self.reframer.reframe(
            "Summarize the topic about Hadoop.",
            subject="Big Data",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.SUMMARY,
        )
        self.assertEqual(
            result.output_format,
            ReframerOutputFormat.SUMMARY,
        )

    def test_detects_comparison(self):
        result = self.reframer.reframe(
            "Compare paging and segmentation.",
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.COMPARISON,
        )
        self.assertEqual(
            result.output_format,
            ReframerOutputFormat.COMPARISON_TABLE,
        )

    def test_detects_explanation(self):
        result = self.reframer.reframe(
            "Explain virtual memory.",
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.EXPLANATION,
        )

    def test_detects_practice_questions(self):
        result = self.reframer.reframe(
            "Give me 20 important questions for the exam.",
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.PRACTICE_QUESTIONS,
        )
        self.assertEqual(
            result.output_format,
            ReframerOutputFormat.PRACTICE_SET,
        )
        self.assertIn(
            "20 questions",
            result.constraints,
        )

    def test_preserves_original_question(self):
        question = "Explain deadlock prevention in detail."

        result = self.reframer.reframe(
            question,
            subject="Operating System",
        )

        self.assertEqual(
            result.original_question,
            question,
        )
        self.assertIn(
            "detailed explanation",
            result.constraints,
        )

    def test_subject_is_used_when_no_narrower_topic_exists(self):
        result = self.reframer.reframe(
            "What are the important topics?",
            subject="Big Data Analytics",
        )

        self.assertEqual(
            result.topic,
            "Big Data Analytics",
        )

    def test_explicit_topic_is_extracted(self):
        result = self.reframer.reframe(
            "Summarize the topic about MapReduce.",
            subject="Big Data Analytics",
        )

        self.assertEqual(
            result.topic,
            "MapReduce",
        )

    def test_empty_question_is_rejected(self):
        with self.assertRaises(ValueError):
            self.reframer.reframe("")

    def test_non_string_question_is_rejected(self):
        with self.assertRaises(ValueError):
            self.reframer.reframe(None)

    def test_unknown_intent_is_not_fabricated(self):
        result = self.reframer.reframe(
            "important ones",
            subject="Big Data Analytics",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.GENERAL_QA,
        )

    # ---------------------------------------------------------
    # Step 5B.2 - LLM-assisted reframing
    # ---------------------------------------------------------

    def _build_llm_result(
        self,
        *,
        question,
        intent=ReframerIntent.EXPLANATION,
        topic="Virtual Memory",
        output_format=ReframerOutputFormat.EXPLANATION,
        constraints=("detailed explanation",),
        clarification_needed=False,
        confidence=0.92,
    ):
        return PromptReframerResult(
            original_question=question,
            intent=intent,
            topic=topic,
            output_format=output_format,
            constraints=tuple(constraints),
            clarification_needed=clarification_needed,
            confidence=confidence,
        )

    def test_high_confidence_does_not_call_llm(self):
        llm_reframer = MagicMock()

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            "Explain virtual memory.",
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.EXPLANATION,
        )

        llm_reframer.reframe.assert_not_called()

    def test_high_confidence_is_above_threshold(self):
        self.assertEqual(
            LLM_REFRAME_CONFIDENCE_THRESHOLD,
            0.75,
        )

    def test_low_confidence_calls_llm(self):
        llm_reframer = MagicMock()

        question = "What is this?"

        fallback = PromptReframer().reframe(
            question,
            subject="Operating System",
        )

        llm_reframer.reframe.return_value = (
            self._build_llm_result(
                question=question,
                intent=ReframerIntent.EXPLANATION,
                topic="Operating System",
                output_format=ReframerOutputFormat.EXPLANATION,
                constraints=(),
                confidence=0.91,
            )
        )

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            question,
            subject="Operating System",
        )

        llm_reframer.reframe.assert_called_once_with(
            question=question,
            subject="Operating System",
            fallback=fallback,
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.EXPLANATION,
        )

    def test_llm_result_preserves_original_question(self):
        llm_reframer = MagicMock()

        question = "What is this?"

        llm_result = self._build_llm_result(
            question=question,
        )

        llm_reframer.reframe.return_value = (
            llm_result
        )

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            question,
            subject="Operating System",
        )

        self.assertEqual(
            result.original_question,
            question,
        )

    def test_invalid_llm_result_falls_back_to_deterministic(self):
        llm_reframer = MagicMock()

        question = "What is this?"

        llm_reframer.reframe.return_value = (
            "not a reframer result"
        )

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            question,
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.GENERAL_QA,
        )
        self.assertEqual(
            result.confidence,
            0.55,
        )

    def test_llm_failure_falls_back_to_deterministic(self):
        llm_reframer = MagicMock()

        llm_reframer.reframe.side_effect = (
            RuntimeError("provider failed")
        )

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            "What is this?",
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.GENERAL_QA,
        )

    def test_llm_result_with_different_original_question_is_rejected(self):
        llm_reframer = MagicMock()

        llm_reframer.reframe.return_value = (
            self._build_llm_result(
                question="Different question",
            )
        )

        question = "What is this?"

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            question,
            subject="Operating System",
        )

        self.assertEqual(
            result.original_question,
            question,
        )
        self.assertEqual(
            result.intent,
            ReframerIntent.GENERAL_QA,
        )

    def test_llm_is_not_called_for_clear_practice_question(self):
        llm_reframer = MagicMock()

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            "Give me 10 exam questions.",
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.PRACTICE_QUESTIONS,
        )

        llm_reframer.reframe.assert_not_called()

    def test_llm_result_can_change_low_confidence_intent(self):
        llm_reframer = MagicMock()

        question = "What is this?"

        llm_reframer.reframe.return_value = (
            self._build_llm_result(
                question=question,
                intent=ReframerIntent.EXPLANATION,
                topic="Operating System",
                output_format=ReframerOutputFormat.EXPLANATION,
                constraints=(),
                confidence=0.88,
            )
        )

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            question,
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.EXPLANATION,
        )

    def test_no_llm_means_deterministic_behavior_is_preserved(self):
        reframer = PromptReframer()

        result = reframer.reframe(
            "What is this?",
            subject="Operating System",
        )

        self.assertEqual(
            result.intent,
            ReframerIntent.GENERAL_QA,
        )
        self.assertEqual(
            result.output_format,
            ReframerOutputFormat.DEFAULT,
        )

    def test_llm_contract_accepts_structured_result_only(self):
        llm_reframer = MagicMock()

        question = "What is this?"

        llm_reframer.reframe.return_value = (
            self._build_llm_result(
                question=question,
            )
        )

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            question,
            subject="Operating System",
        )

        self.assertIsInstance(
            result,
            PromptReframerResult,
        )

    def test_reframer_does_not_generate_academic_answer(self):
        llm_reframer = MagicMock()

        question = "What is this?"

        llm_reframer.reframe.return_value = (
            self._build_llm_result(
                question=question,
            )
        )

        reframer = PromptReframer(
            llm_reframer=llm_reframer,
        )

        result = reframer.reframe(
            question,
            subject="Operating System",
        )

        self.assertFalse(
            hasattr(result, "answer")
        )
        self.assertEqual(
            result.original_question,
            question,
        )