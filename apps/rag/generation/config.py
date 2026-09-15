from django.conf import settings


DEFAULT_MAX_CONTEXT_CHUNKS = 5
MAX_ALLOWED_CONTEXT_CHUNKS = 20

DEFAULT_MAX_CONTEXT_CHARACTERS = 12000
MAX_ALLOWED_CONTEXT_CHARACTERS = 50000

DEFAULT_GROQ_MODEL = ""

DEFAULT_GEMINI_MODEL = ""

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"


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


def get_gemini_api_key():
    return getattr(
        settings,
        "GEMINI_API_KEY",
        "",
    )


def get_gemini_model():
    return getattr(
        settings,
        "GEMINI_MODEL",
        DEFAULT_GEMINI_MODEL,
    )


def get_ollama_base_url():
    return getattr(
        settings,
        "OLLAMA_BASE_URL",
        DEFAULT_OLLAMA_BASE_URL,
    )


def get_ollama_model():
    return getattr(
        settings,
        "OLLAMA_MODEL",
        DEFAULT_OLLAMA_MODEL,
    )