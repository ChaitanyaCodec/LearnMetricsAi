"""
Dashboard service layer: aggregate selectors and provide dashboard context.
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
    get_teacher_dashboard_data,
    get_student_dashboard_data,
)


def get_system_status() -> dict[str, Any]:
    # Database/auth values are placeholders until live health probes are wired.
    return {
        "database": {"status": "success", "label": "Configured"},
        "authentication": {"status": "success", "label": "Operational"},
        "ai_module": {"status": "warning", "label": "Provider status not checked"},
        "background_tasks": {"status": "warning", "label": "Not configured"},
        "overall": {"status": "warning", "label": "Some integrations not monitored"},
    }


def get_admin_dashboard_statistics() -> dict[str, Any]:
    return {
        "total_students": get_total_students(),
        "total_teachers": get_total_teachers(),
        "total_admins": get_total_admins(),
        "active_users": get_active_users_count(),
        "recent_users": get_recent_users(limit=10),
        "recent_logins": get_recently_active_users(limit=10),
        "system_status": get_system_status(),
    }


def get_teacher_dashboard_statistics(user) -> dict[str, Any]:
    context = get_teacher_dashboard_data(user)
    context["demo_features"] = [
        {
            "title": "Attendance insights",
            "value": "Demo: 92%",
            "description": "Sample class attendance rate. Live attendance records are not connected.",
        },
        {
            "title": "Assignments to review",
            "value": "Demo: 8",
            "description": "Sample count only. Assignment/submission management is not connected.",
        },
        {
            "title": "Upcoming classes",
            "value": "Demo: 3",
            "description": "Sample schedule only. A teaching calendar is not connected.",
        },
        {
            "title": "Class performance",
            "value": "Demo: 78/100",
            "description": "Sample score only. Live marks and analytics are not connected.",
        },
    ]
    return context


def get_student_dashboard_statistics(user) -> dict[str, Any]:
    context = get_student_dashboard_data(user)
    context["demo_features"] = [
        {
            "title": "Attendance",
            "value": "Demo: 92%",
            "description": "Illustrative only. Personal attendance records are not connected.",
        },
        {
            "title": "Assignments due",
            "value": "Demo: 2",
            "description": "Illustrative only. Assignment/deadline records are not connected.",
        },
        {
            "title": "Current average",
            "value": "Demo: 81%",
            "description": "Illustrative only. Student marks and grades are not connected.",
        },
        {
            "title": "Study goal",
            "value": "Demo: 4 hours/week",
            "description": "Illustrative only. Personalized study planning is not connected.",
        },
    ]
    return context
