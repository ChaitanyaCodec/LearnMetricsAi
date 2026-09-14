from dataclasses import dataclass

from .embeddings import EmbeddingService
from .generation import AnswerGenerationService
from .retrieval import RetrievalService


class RagServiceError(Exception):
    """Base exception for RAG service failures."""


@dataclass(frozen=True)
class RagAnswer:
    """
    Structured result produced by the RAG pipeline.

    The retrieved chunks are retained so callers can expose
    deterministic source metadata without relying on the LLM
    to identify or reproduce citations.
    """

    answer: str
    chunks: tuple


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
        Conversation Context
            ↓
        Answer Generation
            ↓
        Answer + Retrieved Sources
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
        self._validate_question(question)

        try:
            query_embedding = (
                self.embedding_service.embed_text(
                    question.strip()
                )
            )
        except Exception as exc:
            raise RagServiceError(
                "Failed to generate question embedding."
            ) from exc

        retrieval_kwargs = {
            "query_embedding": query_embedding,
            "subject": subject,
        }

        if top_k is not None:
            retrieval_kwargs["top_k"] = top_k

        try:
            return self.retrieval_service.retrieve(
                **retrieval_kwargs
            )
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
        conversation_history=None,
    ):
        result = self.answer_question_with_sources(
            user=user,
            question=question,
            subject=subject,
            top_k=top_k,
            conversation_history=conversation_history,
        )

        return result.answer

    def answer_question_with_sources(
        self,
        *,
        user=None,
        question,
        subject=None,
        top_k=None,
        conversation_history=None,
    ):
        self._validate_question(question)

        retrieve_kwargs = {
            "question": question,
            "subject": subject,
        }

        if top_k is not None:
            retrieve_kwargs["top_k"] = top_k

        chunks = self.retrieve_question(
            **retrieve_kwargs
        )

        if chunks is None:
            raise RagServiceError(
                "Retrieved chunks are required."
            )

        chunks = tuple(chunks)

        generation_kwargs = {
            "question": question.strip(),
            "chunks": chunks,
        }

        if conversation_history is not None:
            generation_kwargs[
                "conversation_history"
            ] = conversation_history

        try:
            answer = self.generation_service.generate(
                **generation_kwargs
            )
        except Exception as exc:
            raise RagServiceError(
                "Failed to generate an answer."
            ) from exc

        return RagAnswer(
            answer=answer,
            chunks=chunks,
        )

    @staticmethod
    def _validate_question(question):
        if not isinstance(question, str):
            raise RagServiceError(
                "Question must be a string."
            )

        if not question.strip():
            raise RagServiceError(
                "Question cannot be empty."
            )