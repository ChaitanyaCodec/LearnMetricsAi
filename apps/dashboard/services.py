"""
Dashboard service layer.

This module contains business logic for dashboard functionality.

Responsibilities:
- Aggregate selector results
- Apply business rules
- Prepare dashboard-ready data
- Remain independent of Django views/templates
"""

from __future__ import annotations

from typing import Any

from .selectors import (
    get_active_users_count,
    get_recent_users,
    get_recently_active_users,
    get_total_admins,
    get_total_students,
    get_total_teachers,
)


def get_system_status() -> dict[str, Any]:
    """
    Return high-level system health information.

    This is intentionally simple for now and can later include:
    - Redis connectivity
    - Celery worker status
    - AI service availability
    - Database health
    - Storage usage
    """

    def get_system_status():
        return {
    "database": {
        "status": "success",
        "label": "Connected",
    },
    "authentication": {
        "status": "success",
        "label": "Operational",
    },
    "ai_module": {
        "status": "warning",
        "label": "Coming Soon",
    },
    "background_tasks": {
        "status": "warning",
        "label": "Not Configured",
    },
    "overall": {
        "status": "success",
        "label": "Healthy",
    },
}


def get_admin_dashboard_statistics() -> dict[str, Any]:
    """
    Aggregate all data required for the administrator dashboard.

    This function represents the public interface used by the view.
    """

    total_students = get_total_students()
    total_teachers = get_total_teachers()
    total_admins = get_total_admins()
    active_users = get_active_users_count()

    recent_users = get_recent_users(limit=10)
    recent_logins = get_recently_active_users(limit=10)

    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_admins": total_admins,
        "active_users": active_users,
        "recent_users": recent_users,
        "recent_logins": recent_logins,
        "system_status": get_system_status(),
    }
