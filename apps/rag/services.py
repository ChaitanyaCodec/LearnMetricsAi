from .embeddings import EmbeddingService
from .generation import AnswerGenerationService
from .retrieval import RetrievalService


class RagServiceError(Exception):
    """
    Base exception for RAG service failures.
    """


class RagService:
    """
    Central orchestration service for the RAG pipeline.

    Pipeline:
        Question
            ↓
        Embedding
            ↓
        Vector Retrieval
            ↓
        Answer Generation
    """

    def __init__(
        self,
        *,
        embedding_service=None,
        retrieval_service=None,
        generation_service=None,
    ):
        self.embedding_service = (
            embedding_service
            if embedding_service is not None
            else EmbeddingService()
        )

        self.retrieval_service = (
            retrieval_service
            if retrieval_service is not None
            else RetrievalService()
        )

        self.generation_service = (
            generation_service
            if generation_service is not None
            else AnswerGenerationService()
        )

    def retrieve_question(
        self,
        *,
        question,
        top_k=None,
        subject=None,
    ):
        """
        Convert a question into an embedding and retrieve
        the most relevant document chunks.
        """

        self._validate_question(question)

        try:
            query_embedding = self.embedding_service.embed_text(
                question.strip()
            )
        except Exception as exc:
            raise RagServiceError(
                "Failed to generate question embedding."
            ) from exc

        # Build retrieval kwargs dynamically so omitted default values 
        # do not pollute mock verification calls
        retrieval_kwargs = {
            "query_embedding": query_embedding,
            "subject": subject,
        }
        if top_k is not None:
            retrieval_kwargs["top_k"] = top_k

        try:
            return self.retrieval_service.retrieve(**retrieval_kwargs)
        except Exception as exc:
            raise RagServiceError(
                "Failed to retrieve relevant document chunks."
            ) from exc

    def answer_question(
        self,
        *,
        user=None,
        question,
        subject=None,
        top_k=None,
    ):
        """
        Execute the complete RAG question-answering pipeline.

        1. Validate the question.
        2. Generate its embedding.
        3. Retrieve relevant chunks.
        4. Generate an answer from those chunks.
        """

        self._validate_question(question)

        retrieve_kwargs = {
            "question": question,
            "subject": subject,
        }
        if top_k is not None:
            retrieve_kwargs["top_k"] = top_k

        chunks = self.retrieve_question(**retrieve_kwargs)

        try:
            return self.generation_service.generate(
                question=question.strip(),
                chunks=chunks,
            )
        except Exception as exc:
            raise RagServiceError(
                "Failed to generate an answer."
            ) from exc

    @staticmethod
    def _validate_question(question):
        """
        Validate the user's question.
        """

        if not isinstance(question, str):
            raise RagServiceError(
                "Question must be a string."
            )

        if not question.strip():
            raise RagServiceError(
                "Question cannot be empty."
            )