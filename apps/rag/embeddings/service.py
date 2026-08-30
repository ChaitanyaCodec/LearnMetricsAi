from .exceptions import EmbeddingError
from .model import EmbeddingModel


class EmbeddingService:
    """
    Central service for generating text embeddings.
    """

    def __init__(self):
        self.model = EmbeddingModel()

    def embed_text(self, text):
        """
        Generate an embedding for a single text.
        """

        if not isinstance(text, str):
            raise EmbeddingError(
                "Text must be a string."
            )

        if not text.strip():
            raise EmbeddingError(
                "Text cannot be empty."
            )

        try:
            embeddings = self.model.encode([text])

            return embeddings[0].tolist()

        except Exception as exc:
            raise EmbeddingError(
                "Failed to generate embedding."
            ) from exc

    def embed_texts(self, texts):
        """
        Generate embeddings for multiple texts.
        """

        if not isinstance(texts, list):
            raise EmbeddingError(
                "Texts must be provided as a list."
            )

        if not texts:
            return []

        for text in texts:
            if not isinstance(text, str):
                raise EmbeddingError(
                    "Each text must be a string."
                )

            if not text.strip():
                raise EmbeddingError(
                    "Text cannot be empty."
                )

        try:
            embeddings = self.model.encode(texts)

            return embeddings.tolist()

        except Exception as exc:
            raise EmbeddingError(
                "Failed to generate embeddings."
            ) from exc