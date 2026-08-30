class RagServiceError(Exception):
    """
    Base exception for RAG service failures.
    """

class RagService:
    """
    Central entry point for RAG operations.

    Retrieval, context construction, and answer generation
    will be implemented in later RAG phases.
    """

    def answer_question(
        self,
        *,
        user,
        question,
        subject=None,
    ):
        raise NotImplementedError(
            "RAG question answering is not implemented yet."
        )