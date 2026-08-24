from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_document_file(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in settings.DOCUMENTS_ALLOWED_EXTENSIONS:
        allowed = ", ".join(settings.DOCUMENTS_ALLOWED_EXTENSIONS)
        raise ValidationError(
            f"Unsupported file type. Allowed types: {allowed}."
        )

    if uploaded_file.size > settings.DOCUMENTS_MAX_UPLOAD_SIZE:
        max_size_mb = settings.DOCUMENTS_MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError(
            f"File must not exceed {max_size_mb} MB."
        )