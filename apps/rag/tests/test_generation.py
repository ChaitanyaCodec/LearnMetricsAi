from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.rag.generation import (
    AnswerGenerationService,
    GenerationError,
)


class AnswerGenerationServiceTests(SimpleTestCase):
    """Tests for the answer generation service."""

    def test_question_must_be_string(self):
        service = AnswerGenerationService(
            provider=Mock(),
        )

        with self.assertRaises(GenerationError):
            service.generate(
                question=123,
                chunks=[],
            )

    def test_empty_question_is_rejected(self):
        service = AnswerGenerationService(
            provider=Mock(),
        )

        with self.assertRaises(GenerationError):
            service.generate(
                question="   ",
                chunks=[],
            )

    def test_none_chunks_are_rejected(self):
        service = AnswerGenerationService(
            provider=Mock(),
        )

        with self.assertRaises(GenerationError):
            service.generate(
                question="What is SQL?",
                chunks=None,
            )

    def test_empty_context_is_rejected(self):
        service = AnswerGenerationService(
            provider=Mock(),
        )

        with self.assertRaises(GenerationError):
            service.generate(
                question="What is SQL?",
                chunks=[],
            )

    def test_provider_generates_answer(self):
        provider = Mock()
        provider.generate.return_value = (
            "SQL is a query language."
        )

        service = AnswerGenerationService(
            provider=provider,
        )

        chunk = Mock()
        chunk.content = (
            "SQL is used to query relational databases."
        )

        result = service.generate(
            question="What is SQL?",
            chunks=[chunk],
        )

        self.assertEqual(
            result,
            "SQL is a query language.",
        )

        provider.generate.assert_called_once()

        prompt = provider.generate.call_args.args[0]

        self.assertIn(
            "What is SQL?",
            prompt,
        )

        self.assertIn(
            "SQL is used to query relational databases.",
            prompt,
        )

    def test_provider_failure_is_wrapped(self):
        provider = Mock()
        provider.generate.side_effect = RuntimeError(
            "provider failure"
        )

        service = AnswerGenerationService(
            provider=provider,
        )

        chunk = Mock()
        chunk.content = "Database content."

        with self.assertRaises(GenerationError):
            service.generate(
                question="What is a database?",
                chunks=[chunk],
            )