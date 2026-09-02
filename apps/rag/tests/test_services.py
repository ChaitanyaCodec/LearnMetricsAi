from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.rag.services import (
    RagService,
    RagServiceError,
)


class RagServiceRetrievalTests(SimpleTestCase):
    """Tests for question-to-retrieval orchestration."""

    def setUp(self):
        self.embedding_service = Mock()
        self.retrieval_service = Mock()
        self.generation_service = Mock()

        self.service = RagService(
            embedding_service=self.embedding_service,
            retrieval_service=self.retrieval_service,
            generation_service=self.generation_service,
        )

    def test_retrieve_question_generates_embedding_and_retrieves(self):
        query_embedding = [0.1] * 384

        expected_results = [
            "chunk-1",
            "chunk-2",
        ]

        self.embedding_service.embed_text.return_value = (
            query_embedding
        )

        self.retrieval_service.retrieve.return_value = (
            expected_results
        )

        results = self.service.retrieve_question(
            question="What is a database?",
            top_k=5,
        )

        self.assertEqual(
            results,
            expected_results,
        )

        self.embedding_service.embed_text.assert_called_once_with(
            "What is a database?"
        )

        self.retrieval_service.retrieve.assert_called_once_with(
            query_embedding=query_embedding,
            top_k=5,
            subject=None,
        )

    def test_subject_is_forwarded(self):
        query_embedding = [0.1] * 384

        self.embedding_service.embed_text.return_value = (
            query_embedding
        )

        self.retrieval_service.retrieve.return_value = []

        subject = Mock()

        self.service.retrieve_question(
            question="What is normalization?",
            top_k=3,
            subject=subject,
        )

        self.retrieval_service.retrieve.assert_called_once_with(
            query_embedding=query_embedding,
            top_k=3,
            subject=subject,
        )

    def test_empty_question_is_rejected(self):
        with self.assertRaises(RagServiceError):
            self.service.answer_question(
                user=None,
                question="",
            )
    def test_whitespace_question_is_rejected(self):
        with self.assertRaises(RagServiceError):
            self.service.answer_question(
                user=None,
                question="   ",
            )

    def test_non_string_question_is_rejected(self):
        with self.assertRaises(RagServiceError):
            self.service.answer_question(
                user=None,
                question=123,
            )

    def test_embedding_failure_is_wrapped(self):
        self.embedding_service.embed_text.side_effect = (
            RuntimeError("embedding failure")
        )

        with self.assertRaises(RagServiceError):
            self.service.answer_question(
                user=None,
                question="What is a database?",
            )

        self.retrieval_service.retrieve.assert_not_called()

        self.generation_service.generate.assert_not_called()
    def test_retrieval_failure_is_wrapped(self):
        self.embedding_service.embed_text.return_value = [
            0.1
        ] * 384

        self.retrieval_service.retrieve.side_effect = (
            RuntimeError("retrieval failure")
        )

        with self.assertRaises(RagServiceError):
            self.service.answer_question(
                user=None,
                question="What is a database?",
            )

        self.generation_service.generate.assert_not_called()

    def test_answer_question_runs_full_pipeline(self):
        self.embedding_service.embed_text.return_value = [
            0.1
        ] * 384

        chunks = [
            Mock(),
            Mock(),
        ]

        self.retrieval_service.retrieve.return_value = chunks

        self.generation_service.generate.return_value = (
            "A database is an organized collection of data."
        )

        result = self.service.answer_question(
            user=None,
            question="  What is a database?  ",
        )

        self.assertEqual(
            result,
            "A database is an organized collection of data.",
        )

        self.embedding_service.embed_text.assert_called_once_with(
            "What is a database?"
        )

        self.retrieval_service.retrieve.assert_called_once_with(
            query_embedding=[0.1] * 384,
            subject=None,
        )

        self.generation_service.generate.assert_called_once_with(
            question="What is a database?",
            chunks=chunks,
        )
    def test_subject_is_forwarded_through_pipeline(self):
        subject = Mock()

        self.embedding_service.embed_text.return_value = [
            0.1
        ] * 384

        chunks = [Mock()]

        self.retrieval_service.retrieve.return_value = chunks

        self.generation_service.generate.return_value = (
            "Answer"
        )

        result = self.service.answer_question(
            user=None,
            question="What is SQL?",
            subject=subject,
        )

        self.assertEqual(
            result,
            "Answer",
        )

        self.retrieval_service.retrieve.assert_called_once_with(
            query_embedding=[0.1] * 384,
            subject=subject,
        )

    def test_generation_failure_is_wrapped(self):
        self.embedding_service.embed_text.return_value = [
            0.1
        ] * 384

        chunks = [Mock()]

        self.retrieval_service.retrieve.return_value = chunks

        self.generation_service.generate.side_effect = (
            RuntimeError("generation failure")
        )

        with self.assertRaises(RagServiceError):
            self.service.answer_question(
                user=None,
                question="What is a database?",
            )