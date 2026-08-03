import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """
    Custom User model for LearnMetrics AI.
    """

    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    username = None

    email = models.EmailField(
        unique=True,
    )

    first_name = models.CharField(
        max_length=150,
    )

    last_name = models.CharField(
        max_length=150,
    )

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STUDENT,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
