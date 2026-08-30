from django.test import SimpleTestCase

from apps.rag.services import RagService


class RagFoundationTests(SimpleTestCase):
    """
    Tests for the RAG application foundation.
    """

    def test_rag_service_exists(self):
        service = RagService()

        self.assertIsNotNone(service)

    def test_question_answering_is_not_implemented_yet(self):
        service = RagService()

        with self.assertRaises(NotImplementedError):
            service.answer_question(
                user=None,
                question="What is a database?",
            )