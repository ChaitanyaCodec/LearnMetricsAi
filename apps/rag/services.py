from dataclasses import dataclass

from .embeddings import EmbeddingService
from .generation import AnswerGenerationService


from .reframing import PromptReframer

from .retrieval import RetrievalService

from .generation.exceptions import GenerationError
from .generation.providers.factory import get_llm_provider
from .reframing.llm import LLMReframer
class RagServiceError(Exception):
    """Base exception for RAG service failures."""


class RagNoRelevantContextError(RagServiceError):
    """
    Raised when retrieval completes successfully but does not
    return relevant document context for the question.
    """


class RagClarificationRequiredError(RagServiceError):
    """
    Raised when the prompt reframer determines that the
    student's question is ambiguous and requires clarification.
    """


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
        Prompt Reframing
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
        reframer=None,
        enable_llm_reframing=False,
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

        if reframer is not None:
            self.reframer = reframer
        elif enable_llm_reframing:
            self.reframer = self._build_llm_reframer()
        else:
            self.reframer = PromptReframer()

    @staticmethod
    def _build_llm_reframer():
        try:
            provider_manager = get_llm_provider()

            return PromptReframer(
                llm_reframer=LLMReframer(
                    provider_manager=provider_manager
                )
            )

        except GenerationError:
            return PromptReframer()


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

        reframing_subject = None

        if subject is not None:
            if isinstance(subject, str):
                reframing_subject = subject
            else:
                reframing_subject = getattr(
                    subject,
                    "name",
                    None,
                )

        reframing_result = self.reframer.reframe(
            question=question,
            subject=reframing_subject,
        )

        if reframing_result.clarification_needed:
            raise RagClarificationRequiredError(
                "The question needs clarification before "
                "retrieval can continue."
            )

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

        if not chunks:
            raise RagNoRelevantContextError(
                "No relevant study material was found "
                "for this question."
            )

        generation_kwargs = {
            "question": question.strip(),
            "chunks": chunks,
            "reframing_result": reframing_result,
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
