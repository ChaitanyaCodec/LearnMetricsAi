from django.conf import settings


DEFAULT_TOP_K = 5

MAX_TOP_K = 20

DEFAULT_MAX_DISTANCE = 0.60

MAX_ALLOWED_DISTANCE = 1.0


def get_default_top_k():
    return getattr(
        settings,
        "RAG_RETRIEVAL_TOP_K",
        DEFAULT_TOP_K,
    )


def get_max_distance():
    return getattr(
        settings,
        "RAG_RETRIEVAL_MAX_DISTANCE",
        DEFAULT_MAX_DISTANCE,
    )