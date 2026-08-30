from django.test import SimpleTestCase, override_settings

from apps.rag.embeddings.config import (
    EmbeddingConfigurationError,
    validate_embedding_configuration,
)


class EmbeddingConfigurationTests(SimpleTestCase):

    def test_valid_configuration(self):
        validate_embedding_configuration()

    @override_settings(
        RAG_EMBEDDING_MODEL=""
    )
    def test_empty_model_name_is_rejected(self):
        with self.assertRaises(EmbeddingConfigurationError):
            validate_embedding_configuration()

    @override_settings(
        RAG_EMBEDDING_DIMENSIONS=0
    )
    def test_zero_dimensions_are_rejected(self):
        with self.assertRaises(EmbeddingConfigurationError):
            validate_embedding_configuration()

    @override_settings(
        RAG_EMBEDDING_DIMENSIONS=-384
    )
    def test_negative_dimensions_are_rejected(self):
        with self.assertRaises(EmbeddingConfigurationError):
            validate_embedding_configuration()