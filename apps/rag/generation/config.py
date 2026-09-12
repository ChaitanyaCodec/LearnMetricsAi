from django.conf import settings


DEFAULT_MAX_CONTEXT_CHUNKS = 5
DEFAULT_MAX_CONTEXT_CHARACTERS = 12000

DEFAULT_GROQ_MODEL = ""


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


def get_groq_api_key():
    return getattr(
        settings,
        "GROQ_API_KEY",
        "",
    )


def get_groq_model():
    return getattr(
        settings,
        "GROQ_MODEL",
        DEFAULT_GROQ_MODEL,
    )