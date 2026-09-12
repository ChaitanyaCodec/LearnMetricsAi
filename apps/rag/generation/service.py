from .config import (
    get_max_context_characters,
    get_max_context_chunks,
)
from .exceptions import GenerationError
from .providers.factory import get_llm_provider


class AnswerGenerationService:
    """
    Builds a grounded generation prompt from retrieved
    document chunks and generates an answer using the
    configured LLM provider chain.

    Provider selection and fallback are handled by the
    provider factory and manager.
    """

    def __init__(self, provider=None):
        self.provider = (
            provider
            if provider is not None
            else get_llm_provider()
        )

    def generate(
        self,
        *,
        question,
        chunks,
    ):
        self._validate_question(question)

        if chunks is None:
            raise GenerationError(
                "Retrieved chunks are required."
            )

        chunks = list(chunks)

        max_chunks = get_max_context_chunks()

        if len(chunks) > max_chunks:
            chunks = chunks[:max_chunks]

        context = self._build_context(chunks)

        if not context:
            raise GenerationError(
                "No usable context was retrieved."
            )

        prompt = self._build_prompt(
            question=question,
            context=context,
        )

        try:
            return self.provider.generate(prompt)
        except GenerationError:
            raise
        except Exception as exc:
            raise GenerationError(
                "Failed to generate an answer."
            ) from exc

    @staticmethod
    def _validate_question(question):
        if not isinstance(question, str):
            raise GenerationError(
                "Question must be a string."
            )

        if not question.strip():
            raise GenerationError(
                "Question cannot be empty."
            )

    @staticmethod
    def _build_context(chunks):
        max_characters = get_max_context_characters()

        parts = []
        total_characters = 0

        for index, chunk in enumerate(chunks, start=1):
            content = getattr(chunk, "content", None)

            if not isinstance(content, str):
                continue

            content = content.strip()

            if not content:
                continue

            remaining = max_characters - total_characters

            if remaining <= 0:
                break

            content = content[:remaining]

            parts.append(
                f"[Source {index}]\n{content}"
            )

            total_characters += len(content)

        return "\n\n".join(parts)

    @staticmethod
    def _build_prompt(*, question, context):
        return (
            "You are an educational assistant for LearnMetrics AI.\n"
            "Answer the student's question using only the provided "
            "context.\n"
            "If the context does not contain enough information, "
            "clearly say that the information is not available "
            "in the provided documents.\n"
            "Do not invent facts.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{question.strip()}\n\n"
            "ANSWER:"
        )