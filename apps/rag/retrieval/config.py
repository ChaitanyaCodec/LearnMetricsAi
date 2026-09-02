from django.conf import settings


DEFAULT_TOP_K = 5
MAX_TOP_K = 20


def get_default_top_k():
    return getattr(
        settings,
        "RAG_RETRIEVAL_TOP_K",
        DEFAULT_TOP_K,
    )