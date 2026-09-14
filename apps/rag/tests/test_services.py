from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.rag.services import (
    RagAnswer,
    RagService,
    RagServiceError,
)


class RagServiceTests(SimpleTestCase):
    def setUp(self):
        self.embedding_service = Mock()
        self.retrieval_service = Mock()
        self.generation_service = Mock()

        self.service = RagService(
            embedding_service=self.embedding_service,
            retrieval_service=self.retrieval_service,
            generation_service=self.generation_service,
        )

    def test_question_must_be_string(self):
        with self.assertRaises(RagServiceError):
            self.service.retrieve_question(
                question=123
            )

    def test_empty_question_is_rejected(self):
        with self.assertRaises(RagServiceError):
            self.service.retrieve_question(
                question="   "
            )

    def test_embedding_failure_is_wrapped(self):
        self.embedding_service.embed_text.side_effect = Exception(
            "Embedding failed"
        )

        with self.assertRaises(RagServiceError):
            self.service.retrieve_question(
                question="What is normalization?"
            )

    def test_retrieval_failure_is_wrapped(self):
        self.embedding_service.embed_text.return_value = [
            0.1,
            0.2,
        ]

        self.retrieval_service.retrieve.side_effect = Exception(
            "Retrieval failed"
        )

        with self.assertRaises(RagServiceError):
            self.service.retrieve_question(
                question="What is normalization?"
            )

    def test_retrieval_pipeline(self):
        embedding = [0.1, 0.2]
        chunks = [
            SimpleNamespace(content="Normalization content")
        ]

        self.embedding_service.embed_text.return_value = embedding
        self.retrieval_service.retrieve.return_value = chunks

        result = self.service.retrieve_question(
            question="What is normalization?",
            top_k=5,
            subject="subject",
        )

        self.assertEqual(result, chunks)

        self.embedding_service.embed_text.assert_called_once_with(
            "What is normalization?"
        )

        self.retrieval_service.retrieve.assert_called_once_with(
            query_embedding=embedding,
            subject="subject",
            top_k=5,
        )

    def test_subject_is_forwarded(self):
        embedding = [0.1, 0.2]

        self.embedding_service.embed_text.return_value = embedding
        self.retrieval_service.retrieve.return_value = []

        self.service.retrieve_question(
            question="What is normalization?",
            subject="subject",
        )

        self.retrieval_service.retrieve.assert_called_once_with(
            query_embedding=embedding,
            subject="subject",
        )

    def test_answer_question_returns_answer(self):
        chunks = [
            SimpleNamespace(content="Normalization content")
        ]

        self.embedding_service.embed_text.return_value = [
            0.1,
            0.2,
        ]
        self.retrieval_service.retrieve.return_value = chunks
        self.generation_service.generate.return_value = (
            "Normalization is the organization of data."
        )

        result = self.service.answer_question(
            question="What is normalization?",
            subject="subject",
            top_k=5,
        )

        self.assertEqual(
            result,
            "Normalization is the organization of data.",
        )

        self.generation_service.generate.assert_called_once_with(
            question="What is normalization?",
            chunks=tuple(chunks),
        )

    def test_generation_failure_is_wrapped(self):
        chunks = [
            SimpleNamespace(content="Normalization content")
        ]

        self.embedding_service.embed_text.return_value = [
            0.1,
            0.2,
        ]
        self.retrieval_service.retrieve.return_value = chunks
        self.generation_service.generate.side_effect = Exception(
            "Generation failed"
        )

        with self.assertRaises(RagServiceError):
            self.service.answer_question(
                question="What is normalization?"
            )

    def test_subject_is_forwarded_through_answer_pipeline(self):
        chunks = [
            SimpleNamespace(content="Normalization content")
        ]

        self.embedding_service.embed_text.return_value = [
            0.1,
            0.2,
        ]
        self.retrieval_service.retrieve.return_value = chunks
        self.generation_service.generate.return_value = "Answer"

        self.service.answer_question(
            question="What is normalization?",
            subject="subject",
            top_k=3,
        )

        self.retrieval_service.retrieve.assert_called_once_with(
            query_embedding=[0.1, 0.2],
            subject="subject",
            top_k=3,
        )

    def test_answer_question_with_sources_returns_structured_result(
        self,
    ):
        chunk = SimpleNamespace(
            content="Normalization content"
        )

        self.embedding_service.embed_text.return_value = [
            0.1,
            0.2,
        ]
        self.retrieval_service.retrieve.return_value = [
            chunk
        ]
        self.generation_service.generate.return_value = (
            "Normalization is the organization of data."
        )

        result = self.service.answer_question_with_sources(
            question="What is normalization?",
            subject="subject",
            top_k=5,
        )

        self.assertIsInstance(result, RagAnswer)

        self.assertEqual(
            result.answer,
            "Normalization is the organization of data.",
        )

        self.assertEqual(
            result.chunks,
            (chunk,),
        )

        self.generation_service.generate.assert_called_once_with(
            question="What is normalization?",
            chunks=(chunk,),
        )

    def test_answer_question_with_sources_preserves_retrieved_chunks(
        self,
    ):
        first_chunk = SimpleNamespace(
            content="First source"
        )
        second_chunk = SimpleNamespace(
            content="Second source"
        )

        retrieved_chunks = [
            first_chunk,
            second_chunk,
        ]

        self.embedding_service.embed_text.return_value = [
            0.1,
            0.2,
        ]
        self.retrieval_service.retrieve.return_value = (
            retrieved_chunks
        )
        self.generation_service.generate.return_value = "Answer"

        result = self.service.answer_question_with_sources(
            question="Question?"
        )

        self.assertEqual(
            result.chunks,
            (
                first_chunk,
                second_chunk,
            ),
        )

        self.generation_service.generate.assert_called_once_with(
            question="Question?",
            chunks=(
                first_chunk,
                second_chunk,
            ),
        )


    def test_conversation_history_is_forwarded_to_generation(self):
        embedding_service = Mock()
        retrieval_service = Mock()
        generation_service = Mock()

        embedding_service.embed_text.return_value = [
            0.1,
            0.2,
            0.3,
        ]

        chunk = Mock()
        retrieval_service.retrieve.return_value = [chunk]

        generation_service.generate.return_value = (
            "AES supports 128, 192, and 256-bit keys."
        )

        service = RagService(
            embedding_service=embedding_service,
            retrieval_service=retrieval_service,
            generation_service=generation_service,
        )

        history = [
            Mock(
                role="user",
                content="What is AES?",
            ),
            Mock(
                role="assistant",
                content=(
                    "AES is a symmetric encryption algorithm."
                ),
            ),
        ]

        result = service.answer_question_with_sources(
            question="What key sizes does it support?",
            subject=None,
            conversation_history=history,
        )

        self.assertEqual(
            result.answer,
            "AES supports 128, 192, and 256-bit keys.",
        )

        generation_service.generate.assert_called_once_with(
            question="What key sizes does it support?",
            chunks=(chunk,),
            conversation_history=history,
        )