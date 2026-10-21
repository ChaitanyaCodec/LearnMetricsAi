"""
Base Django settings for LearnMetrics AI.

PostgreSQL is required. This configuration intentionally has no SQLite fallback.
"""

from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# -----------------------------------------------------------------------------
# Security / debug
# -----------------------------------------------------------------------------

SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)

# -----------------------------------------------------------------------------
# Application definition
# -----------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
    "apps.dashboard",
    "apps.academics",
    "apps.students",
    "apps.teachers",
    "apps.documents",
    "apps.rag",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Login and logout settings
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/auth/login/"

# -----------------------------------------------------------------------------
# Database — PostgreSQL only
# -----------------------------------------------------------------------------

# DATABASE_URL must be configured in .env. Example format:
# DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
# Use the exact Supabase Session Pooler username and URL-encode special
# characters in the password. Never commit .env to source control.

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

if DATABASES["default"].get("ENGINE") != "django.db.backends.postgresql":
    raise ImproperlyConfigured(
        "LearnMetrics AI requires PostgreSQL. "
        "Set DATABASE_URL to a PostgreSQL connection string in .env."
    )

# Custom user model
AUTH_USER_MODEL = "accounts.User"

# -----------------------------------------------------------------------------
# Password validation
# -----------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static and media files
# -----------------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------------
# Documents app settings
# -----------------------------------------------------------------------------

DOCUMENTS_MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB

DOCUMENTS_ALLOWED_EXTENSIONS = (
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
)

DOCUMENTS_CHUNK_SIZE = 1000
DOCUMENTS_CHUNK_OVERLAP = 150

PRIVATE_DOCUMENTS_ROOT = BASE_DIR / "private_documents"

# -----------------------------------------------------------------------------
# RAG / embedding settings
# -----------------------------------------------------------------------------

RAG_EMBEDDING_MODEL = env.str(
    "RAG_EMBEDDING_MODEL",
    default="all-MiniLM-L6-v2",
)
RAG_EMBEDDING_DIMENSIONS = env.int(
    "RAG_EMBEDDING_DIMENSIONS",
    default=384,
)

RAG_INDEXING_BATCH_SIZE = 32
RAG_INDEXING_MAX_CHUNK_LENGTH = 10000

RAG_GENERATION_MAX_CONTEXT_CHUNKS = env.int(
    "RAG_GENERATION_MAX_CONTEXT_CHUNKS",
    default=5,
)
RAG_GENERATION_MAX_CONTEXT_CHARACTERS = env.int(
    "RAG_GENERATION_MAX_CONTEXT_CHARACTERS",
    default=12000,
)

RAG_RETRIEVAL_TOP_K = env.int(
    "RAG_RETRIEVAL_TOP_K",
    default=5,
)
RAG_RETRIEVAL_MAX_DISTANCE = env.float(
    "RAG_RETRIEVAL_MAX_DISTANCE",
    default=0.60,
)

RAG_CONVERSATION_HISTORY_LIMIT = env.int(
    "RAG_CONVERSATION_HISTORY_LIMIT",
    default=10,
)

# -----------------------------------------------------------------------------
# RAG / LLM provider settings
# -----------------------------------------------------------------------------

GROQ_API_KEY = env.str("GROQ_API_KEY", default="")
GROQ_MODEL = env.str("GROQ_MODEL", default="")

GEMINI_API_KEY = env.str("GEMINI_API_KEY", default="")
GEMINI_MODEL = env.str("GEMINI_MODEL", default="")

OLLAMA_BASE_URL = env.str(
    "OLLAMA_BASE_URL",
    default="http://localhost:11434",
)
OLLAMA_MODEL = env.str(
    "OLLAMA_MODEL",
    default="qwen2.5:3b",
)
