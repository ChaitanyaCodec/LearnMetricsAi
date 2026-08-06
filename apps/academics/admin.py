from django.contrib import admin

from .models import (
    Institution,
    Department,
    Course,
    Semester,
    Subject,
)

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Institution.
    """

    list_display = (
        "name",
        "short_name",
        "email",
        "phone_number",
        "is_active",
    )

    search_fields = (
        "name",
        "short_name",
        "email",
    )

    list_filter = (
        "is_active",
    )

    ordering = (
        "name",
    )

    list_per_page = 25

    readonly_fields = (
        "created_at",
        "updated_at",
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Department.
    list_select_related() should be used.
    """

    list_display = (
        "name",
        "code",
        "institution",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "institution__name",
    )

    list_filter = (
        "institution",
        "is_active",
    )

    ordering = (
        "institution",
        "name",
    )

    list_per_page = 25

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # Optimize ForeignKey lookups in the changelist view.
    # Prevents the N+1 query problem by joining the related
    # Institution table in a single database query.

    list_select_related = (
        "institution",
    )

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Admin configuration for Course.
    """

    list_display = (
        "name",
        "code",
        "department",
        "duration",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "department__name",
    )

    list_filter = (
        "department",
        "is_active",
    )

    ordering = (
        "department",
        "name",
    )

    list_per_page = 25

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # Optimize ForeignKey lookups to avoid N+1 queries.
    list_select_related = (
        "department",
    )

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    """
    Admin configuration for Semester.
    """

    list_display = (
        "name",
        "semester_number",
        "course",
        "is_active",
    )

    search_fields = (
        "name",
        "course__name",
    )

    list_filter = (
        "course",
        "is_active",
    )

    ordering = (
        "course",
        "semester_number",
    )

    list_per_page = 25

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # Optimize ForeignKey lookups to avoid N+1 queries.
    list_select_related = (
        "course",
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """
    Admin configuration for Subject.
    """

    list_display = (
        "code",
        "name",
        "semester",
        "credits",
        "is_active",
    )

    search_fields = (
        "code",
        "name",
        "semester__name",
        "semester__course__name",
    )

    list_filter = (
        "semester",
        "credits",
        "is_active",
    )

    ordering = (
        "semester",
        "name",
    )

    list_per_page = 25

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # Optimize ForeignKey lookups to avoid N+1 queries.
    list_select_related = (
        "semester",
        "semester__course",
    )