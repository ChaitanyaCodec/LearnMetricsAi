from django.test import SimpleTestCase

from apps.rag.services import RagService


class RagFoundationTests(SimpleTestCase):
    """
    Tests for the RAG application foundation.
    """

    def test_rag_service_exists(self):
        service = RagService()

        self.assertIsNotNone(service)