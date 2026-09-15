from django.conf import settings
from django.db.models import F
from pgvector.django import CosineDistance

from apps.documents.models import (
    Document,
    DocumentChunk,
    DocumentVersion,
)

from .config import (
    MAX_ALLOWED_DISTANCE,
    MAX_TOP_K,
    get_default_top_k,
    get_max_distance,
)
from .exceptions import RetrievalError


class RetrievalService:
    """
    Service responsible for retrieving relevant document chunks
    using vector similarity.
    """

    def retrieve(
        self,
        *,
        query_embedding,
        top_k=None,
        subject=None,
    ):
        """
        Retrieve the most relevant indexed chunks.

        Only chunks belonging to active, approved, published,
        processed document versions are considered.

        Chunks exceeding the configured cosine-distance threshold
        are excluded from retrieval.
        """

        self._validate_embedding(query_embedding)

        top_k = self._resolve_top_k(top_k)
        max_distance = self._resolve_max_distance()

        queryset = (
            DocumentChunk.objects
            .filter(
                document_version__document__is_active=True,
                document_version__document__status=(
                    Document.Status.APPROVED
                ),
                document_version__document__published_version_id=F(
                    "document_version_id"
                ),
                document_version__review_status=(
                    DocumentVersion.ReviewStatus.APPROVED
                ),
                document_version__processing_status=(
                    DocumentVersion.ProcessingStatus.COMPLETED
                ),
                embedding_record__isnull=False,
            )
            .annotate(
                distance=CosineDistance(
                    "embedding_record__embedding",
                    query_embedding,
                )
            )
            .select_related(
                "document_version",
                "document_version__document",
                "document_version__document__subject",
            )
            .order_by("distance")
        )

        if subject is not None:
            queryset = queryset.filter(
                document_version__document__subject=subject,
            )

        queryset = queryset.filter(
            distance__lte=max_distance,
        )

        return list(queryset[:top_k])

    @staticmethod
    def _validate_embedding(query_embedding):
        if not isinstance(query_embedding, (list, tuple)):
            raise RetrievalError(
                "Query embedding must be a list or tuple."
            )

        if not query_embedding:
            raise RetrievalError(
                "Query embedding cannot be empty."
            )

        expected_dimensions = settings.RAG_EMBEDDING_DIMENSIONS

        if len(query_embedding) != expected_dimensions:
            raise RetrievalError(
                "Query embedding dimension does not match "
                "the configured RAG embedding dimension."
            )

    @staticmethod
    def _resolve_top_k(top_k):
        if top_k is None:
            top_k = get_default_top_k()

        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise RetrievalError(
                "top_k must be an integer."
            )

        if top_k <= 0:
            raise RetrievalError(
                "top_k must be greater than zero."
            )

        if top_k > MAX_TOP_K:
            raise RetrievalError(
                f"top_k cannot exceed {MAX_TOP_K}."
            )

        return top_k

    @staticmethod
    def _resolve_max_distance():
        max_distance = get_max_distance()

        if isinstance(max_distance, bool):
            raise RetrievalError(
                "Maximum retrieval distance must be a number."
            )

        if not isinstance(max_distance, (int, float)):
            raise RetrievalError(
                "Maximum retrieval distance must be a number."
            )

        if max_distance < 0:
            raise RetrievalError(
                "Maximum retrieval distance cannot be negative."
            )

        if max_distance > MAX_ALLOWED_DISTANCE:
            raise RetrievalError(
                f"Maximum retrieval distance cannot exceed "
                f"{MAX_ALLOWED_DISTANCE}."
            )

        return max_distance