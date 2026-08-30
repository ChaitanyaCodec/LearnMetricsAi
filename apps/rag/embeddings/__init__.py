"""
Embedding functionality for LearnMetrics AI RAG.
"""

from .config import (
    EmbeddingConfigurationError,
    validate_embedding_configuration,
)
from .service import EmbeddingService

__all__ = [
    "EmbeddingService",
    "EmbeddingConfigurationError",
    "validate_embedding_configuration",
]