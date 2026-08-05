from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model providing common fields
    shared across project models.
    """

    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this record is active."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True