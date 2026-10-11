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

    def test_context_chunk_limit_is_enforced(self):
        provider = Mock()
        provider.generate.return_value = "Answer."

        service = AnswerGenerationService(
            provider=provider,
        )

        chunks = []

        for index in range(7):
            chunk = Mock()
            chunk.content = f"Document content {index}."
            chunks.append(chunk)

        with self.settings(
            RAG_GENERATION_MAX_CONTEXT_CHUNKS=2,
        ):
            service.generate(
                question="What is this?",
                chunks=chunks,
            )

        prompt = provider.generate.call_args.args[0]

        self.assertIn(
            "Document content 0.",
            prompt,
        )

        self.assertIn(
            "Document content 1.",
            prompt,
        )

        self.assertNotIn(
            "Document content 2.",
            prompt,
        )

    def test_context_character_limit_is_enforced(self):
        provider = Mock()
        provider.generate.return_value = "Answer."

        service = AnswerGenerationService(
            provider=provider,
        )

        chunk = Mock()
        chunk.content = "A" * 100

        with self.settings(
            RAG_GENERATION_MAX_CONTEXT_CHARACTERS=25,
        ):
            service.generate(
                question="What is this?",
                chunks=[chunk],
            )

        prompt = provider.generate.call_args.args[0]

        self.assertIn(
            "[Source 1]",
            prompt,
        )

        context = prompt.split(
            "RETRIEVED DOCUMENT CONTEXT:\n",
            1,
        )[1].split(
            "\n\nCURRENT QUESTION:",
            1,
        )[0]

        self.assertEqual(
            len(context.split("\n", 1)[1]),
            25,
        )

    def test_invalid_chunks_do_not_create_source_number_gaps(self):
        provider = Mock()
        provider.generate.return_value = "Answer."

        service = AnswerGenerationService(
            provider=provider,
        )

        invalid_chunk = Mock()
        invalid_chunk.content = "   "

        valid_chunk = Mock()
        valid_chunk.content = "Valid document content."

        service.generate(
            question="What is this?",
            chunks=[
                invalid_chunk,
                valid_chunk,
            ],
        )

        prompt = provider.generate.call_args.args[0]

        self.assertIn(
            "[Source 1]\nValid document content.",
            prompt,
        )

        self.assertNotIn(
            "[Source 2]",
            prompt,
        )

    def test_invalid_max_context_chunks_configuration_is_rejected(self):
        service = AnswerGenerationService(
            provider=Mock(),
        )

        chunk = Mock()
        chunk.content = "Document content."

        with self.settings(
            RAG_GENERATION_MAX_CONTEXT_CHUNKS=0,
        ):
            with self.assertRaises(GenerationError):
                service.generate(
                    question="What is this?",
                    chunks=[chunk],
                )

    def test_excessive_max_context_chunks_configuration_is_rejected(self):
        service = AnswerGenerationService(
            provider=Mock(),
        )

        chunk = Mock()
        chunk.content = "Document content."

        with self.settings(
            RAG_GENERATION_MAX_CONTEXT_CHUNKS=21,
        ):
            with self.assertRaises(GenerationError):
                service.generate(
                    question="What is this?",
                    chunks=[chunk],
                )

    def test_invalid_max_context_characters_configuration_is_rejected(self):
        service = AnswerGenerationService(
            provider=Mock(),
        )

        chunk = Mock()
        chunk.content = "Document content."

        with self.settings(
            RAG_GENERATION_MAX_CONTEXT_CHARACTERS=0,
        ):
            with self.assertRaises(GenerationError):
                service.generate(
                    question="What is this?",
                    chunks=[chunk],
                )

    def test_excessive_max_context_characters_configuration_is_rejected(self):
        service = AnswerGenerationService(
            provider=Mock(),
        )

        chunk = Mock()
        chunk.content = "Document content."

        with self.settings(
            RAG_GENERATION_MAX_CONTEXT_CHARACTERS=50001,
        ):
            with self.assertRaises(GenerationError):
                service.generate(
                    question="What is this?",
                    chunks=[chunk],
                )


        def test_reframing_metadata_is_included_in_prompt(self):
            provider = Mock()
            provider.generate.return_value = "Answer."

            service = AnswerGenerationService(
                provider=provider,
            )

            chunk = Mock()
            chunk.content = "Apriori is an association rule mining algorithm."

            reframing_result = Mock()
            reframing_result.intent = "PRACTICE_QUESTIONS"
            reframing_result.topic = "Apriori"
            reframing_result.output_format = "PRACTICE_SET"
            reframing_result.constraints = (
                "10 questions",
            )

            service.generate(
                question="Give me 10 important questions on Apriori.",
                chunks=[chunk],
                reframing_result=reframing_result,
            )

            prompt = provider.generate.call_args.args[0]

            self.assertIn(
                "Intent: PRACTICE_QUESTIONS",
                prompt,
            )

            self.assertIn(
                "Topic: Apriori",
                prompt,
            )

            self.assertIn(
                "Output format: PRACTICE_SET",
                prompt,
            )

            self.assertIn(
                "- 10 questions",
                prompt,
            )

            self.assertIn(
                "Give me 10 important questions on Apriori.",
                prompt,
            )

        def test_reframing_constraints_are_included_in_prompt(self):
            provider = Mock()
            provider.generate.return_value = "Answer."

            service = AnswerGenerationService(
                provider=provider,
            )

            chunk = Mock()
            chunk.content = "Database normalization content."

            reframing_result = Mock()
            reframing_result.intent = "EXPLANATION"
            reframing_result.topic = "Normalization"
            reframing_result.output_format = "EXPLANATION"
            reframing_result.constraints = (
                "detailed explanation",
                "beginner level",
            )

            service.generate(
                question="Explain normalization in detail.",
                chunks=[chunk],
                reframing_result=reframing_result,
            )

            prompt = provider.generate.call_args.args[0]

            self.assertIn(
                "- detailed explanation",
                prompt,
            )

            self.assertIn(
                "- beginner level",
                prompt,
            )

        def test_generation_works_without_reframing(self):
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
            )

            prompt = provider.generate.call_args.args[0]

            self.assertIn(
                "No prompt-reframing metadata available.",
                prompt,
            )

            self.assertIn(
                "What is this?",
                prompt,
            )

        def test_reframing_metadata_does_not_replace_original_question(self):
            provider = Mock()
            provider.generate.return_value = "Answer."

            service = AnswerGenerationService(
                provider=provider,
            )

            chunk = Mock()
            chunk.content = "Apriori content."

            reframing_result = Mock()
            reframing_result.intent = "PRACTICE_QUESTIONS"
            reframing_result.topic = "Apriori"
            reframing_result.output_format = "PRACTICE_SET"
            reframing_result.constraints = (
                "10 questions",
            )

            original_question = (
                "Give me 10 important questions on Apriori."
            )

            service.generate(
                question=original_question,
                chunks=[chunk],
                reframing_result=reframing_result,
            )

            prompt = provider.generate.call_args.args[0]

            self.assertIn(
                f"CURRENT QUESTION:\n{original_question}",
                prompt,
            )

            self.assertNotIn(
                "CURRENT QUESTION:\nApriori",
                prompt,
            )
