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


    def test_conversation_history_is_included_in_prompt(self):
        provider = Mock()
        provider.generate.return_value = (
            "AES supports multiple key sizes."
        )

        service = AnswerGenerationService(
            provider=provider,
        )

        chunk = Mock()
        chunk.content = (
            "AES supports 128-bit, 192-bit, and 256-bit keys."
        )

        user_message = Mock()
        user_message.role = "user"
        user_message.content = "What is AES?"

        assistant_message = Mock()
        assistant_message.role = "assistant"
        assistant_message.content = (
            "AES is a symmetric encryption algorithm."
        )

        service.generate(
            question="What key sizes does it support?",
            chunks=[chunk],
            conversation_history=[
                user_message,
                assistant_message,
            ],
        )

        prompt = provider.generate.call_args.args[0]

        self.assertIn(
            "What is AES?",
            prompt,
        )

        self.assertIn(
            "AES is a symmetric encryption algorithm.",
            prompt,
        )

        self.assertIn(
            "What key sizes does it support?",
            prompt,
        )

        self.assertIn(
            "AES supports 128-bit, 192-bit, and 256-bit keys.",
            prompt,
        )

    def test_empty_conversation_history_is_supported(self):
        provider = Mock()
        provider.generate.return_value = "Answer."

        service = AnswerGenerationService(
            provider=provider,
        )

        chunk = Mock()
        chunk.content = "Document content."

        service.generate(
            question="What is this?",
            chunks=[chunk],
            conversation_history=[],
        )

        prompt = provider.generate.call_args.args[0]

        self.assertIn(
            "No previous conversation.",
            prompt,
        )

    def test_invalid_conversation_history_is_rejected(self):
        provider = Mock()

        service = AnswerGenerationService(
            provider=provider,
        )

        chunk = Mock()
        chunk.content = "Document content."

        with self.assertRaises(GenerationError):
            service.generate(
                question="What is this?",
                chunks=[chunk],
                conversation_history=123,
            )

    def test_history_roles_are_rendered_correctly(self):
        provider = Mock()
        provider.generate.return_value = "Answer."

        service = AnswerGenerationService(
            provider=provider,
        )

        chunk = Mock()
        chunk.content = "Document content."

        user_message = Mock()
        user_message.role = "user"
        user_message.content = "First question"

        assistant_message = Mock()
        assistant_message.role = "assistant"
        assistant_message.content = "First answer"

        service.generate(
            question="Follow-up question",
            chunks=[chunk],
            conversation_history=[
                user_message,
                assistant_message,
            ],
        )

        prompt = provider.generate.call_args.args[0]

        self.assertIn(
            "User: First question",
            prompt,
        )

        self.assertIn(
            "Assistant: First answer",
            prompt,
        )

    def test_invalid_history_messages_are_ignored(self):
        provider = Mock()
        provider.generate.return_value = "Answer."

        service = AnswerGenerationService(
            provider=provider,
        )

        chunk = Mock()
        chunk.content = "Document content."

        invalid_message = Mock()
        invalid_message.role = "system"
        invalid_message.content = "Should not be included."

        service.generate(
            question="What is this?",
            chunks=[chunk],
            conversation_history=[invalid_message],
        )

        prompt = provider.generate.call_args.args[0]

        self.assertNotIn(
            "Should not be included.",
            prompt,
        )

        self.assertIn(
            "No previous conversation.",
            prompt,
        )