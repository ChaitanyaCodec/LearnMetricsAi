"""
Embedding model configuration for LearnMetrics AI.

The actual model loading and embedding generation are kept
separate from the rest of the RAG pipeline.
"""

from django.conf import settings
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Singleton-style wrapper around the configured local
    embedding model.

    The model is loaded once per Django process and reused.
    """

    _model = None

    def __init__(self):
        if self.__class__._model is None:
            self.__class__._model = SentenceTransformer(
                settings.RAG_EMBEDDING_MODEL
            )

    @property
    def model(self):
        return self.__class__._model

    def encode(self, texts):
        """
        Generate normalized embeddings for texts.
        """

        return self.model.encode(
            texts,
            normalize_embeddings=True,
        )

    @property
    def dimensions(self):
        """
        Return configured embedding dimensions.
        """

        return settings.RAG_EMBEDDING_DIMENSIONS