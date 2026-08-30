from django.conf import settings
from django.test import SimpleTestCase

from apps.rag.embeddings import EmbeddingService
from apps.rag.embeddings.exceptions import EmbeddingError




class EmbeddingServiceValidationTests(SimpleTestCase):
    """
    Tests for embedding input validation.
    """

    def setUp(self):
        self.service = object.__new__(EmbeddingService)

    def test_empty_text_is_rejected(self):
        with self.assertRaises(EmbeddingError):
            self.service.embed_text("")

    def test_whitespace_text_is_rejected(self):
        with self.assertRaises(EmbeddingError):
            self.service.embed_text("   ")

    def test_non_string_text_is_rejected(self):
        with self.assertRaises(EmbeddingError):
            self.service.embed_text(None)

    def test_empty_text_list_returns_empty_list(self):
        result = self.service.embed_texts([])

        self.assertEqual(result, [])

    def test_non_list_texts_are_rejected(self):
        with self.assertRaises(EmbeddingError):
            self.service.embed_texts("hello")


class EmbeddingDimensionTests(SimpleTestCase):
    """
    Tests for configured embedding dimensions.
    """

    def test_embedding_dimension_is_384(self):
        self.assertEqual(
            settings.RAG_EMBEDDING_DIMENSIONS,
            384,
        )