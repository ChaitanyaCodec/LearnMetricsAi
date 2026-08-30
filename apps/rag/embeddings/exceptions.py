class EmbeddingError(Exception):
    """
    Base exception for embedding-related failures.
    """
    pass


class EmbeddingModelError(EmbeddingError):
    """
    Raised when the embedding model cannot be loaded or used.
    """