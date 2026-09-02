from django.conf import settings


DEFAULT_MAX_CONTEXT_CHUNKS = 5
DEFAULT_MAX_CONTEXT_CHARACTERS = 12000


def get_max_context_chunks():
    return getattr(
        settings,
        "RAG_GENERATION_MAX_CONTEXT_CHUNKS",
        DEFAULT_MAX_CONTEXT_CHUNKS,
    )


def get_max_context_characters():
    return getattr(
        settings,
        "RAG_GENERATION_MAX_CONTEXT_CHARACTERS",
        DEFAULT_MAX_CONTEXT_CHARACTERS,
    )