"""
Dashboard selectors.

This module contains read-only ORM queries used by dashboard services.

Rules:
- No business logic.
- No writes.
- Optimized queries only.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone

User = get_user_model()


# ---------------------------------------------------------------------
# User Counts
# ---------------------------------------------------------------------

def get_total_students() -> int:
    """
    Return the total number of student users.
    """
    return User.objects.filter(role=User.Role.STUDENT).count()


def get_total_teachers() -> int:
    """
    Return the total number of teacher users.
    """
    return User.objects.filter(role=User.Role.TEACHER).count()


def get_total_admins() -> int:
    """
    Return the total number of administrator users.
    """
    return User.objects.filter(role=User.Role.ADMIN).count()


# ---------------------------------------------------------------------
# Active Users
# ---------------------------------------------------------------------

def get_active_users_count() -> int:
    """
    Return the number of active user accounts.
    """
    return User.objects.filter(is_active=True).count()


# ---------------------------------------------------------------------
# Recent Users
# ---------------------------------------------------------------------

def get_recent_users(limit: int = 10) -> QuerySet[Any]:
    """
    Return recently created users.

    Uses only() to reduce selected columns.
    """

    return (
        User.objects.only(
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "date_joined",
            "is_active",
        )
        .order_by("-date_joined")[:limit]
    )


# ---------------------------------------------------------------------
# Recently Active Users
# ---------------------------------------------------------------------

def get_recently_active_users(limit: int = 10) -> QuerySet[Any]:
    """
    Return users ordered by last login.
    """

    return (
        User.objects.exclude(last_login__isnull=True)
        .only(
            "id",
            "first_name",
            "last_name",
            "email",
            "last_login",
            "role",
        )
        .order_by("-last_login")[:limit]
    )


# ---------------------------------------------------------------------
# New Users Today
# ---------------------------------------------------------------------

def get_new_users_today() -> int:
    """
    Return number of users created today.
    """

    today = timezone.localdate()

    return User.objects.filter(date_joined__date=today).count()