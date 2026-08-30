from django.conf import settings


class EmbeddingConfigurationError(Exception):
    """
    Raised when embedding configuration is invalid.
    """
    pass


def validate_embedding_configuration():
    """
    Validate the configured embedding model settings.
    """

    model_name = settings.RAG_EMBEDDING_MODEL
    dimensions = settings.RAG_EMBEDDING_DIMENSIONS

    if not isinstance(model_name, str) or not model_name.strip():
        raise EmbeddingConfigurationError(
            "RAG_EMBEDDING_MODEL must be a non-empty string."
        )

    if not isinstance(dimensions, int) or dimensions <= 0:
        raise EmbeddingConfigurationError(
            "RAG_EMBEDDING_DIMENSIONS must be a positive integer."
        )