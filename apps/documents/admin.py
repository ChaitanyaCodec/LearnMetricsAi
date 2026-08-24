from django.contrib import admin

from .models import (
    Document,
    DocumentChunk,
    DocumentVersion,
)


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    can_delete = False
    show_change_link = True

    readonly_fields = [
        "version_number",
        "source_file",
        "original_filename",
        "content_type",
        "file_size",
        "file_checksum",
        "uploaded_by",
        "review_status",
        "reviewed_by",
        "reviewed_at",
        "rejection_reason",
        "processing_status",
        "processing_started_at",
        "processing_completed_at",
        "processing_error",
        "page_count",
        "chunk_count",
        "created_at",
        "updated_at",
    ]

    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "subject",
        "status",
        "published_version",
        "created_by",
        "is_active",
        "created_at",
    ]

    list_filter = [
        "status",
        "is_active",
        "subject__semester__course",
        "subject__semester",
    ]

    search_fields = [
        "title",
        "description",
        "subject__name",
        "subject__code",
        "created_by__email",
    ]

    list_select_related = [
        "subject",
        "subject__semester",
        "subject__semester__course",
        "created_by",
        "published_version",
    ]

    readonly_fields = [
        "title",
        "description",
        "subject",
        "status",
        "created_by",
        "published_version",
        "retired_by",
        "retired_at",
        "retirement_reason",
        "is_active",
        "created_at",
        "updated_at",
    ]

    fields = readonly_fields
    inlines = [DocumentVersionInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = [
        "document",
        "version_number",
        "original_filename",
        "processing_status",
        "review_status",
        "uploaded_by",
        "created_at",
    ]

    list_filter = [
        "processing_status",
        "review_status",
    ]

    search_fields = [
        "document__title",
        "original_filename",
        "uploaded_by__email",
    ]

    list_select_related = [
        "document",
        "uploaded_by",
        "reviewed_by",
    ]

    readonly_fields = [
        "document",
        "version_number",
        "source_file",
        "original_filename",
        "content_type",
        "file_size",
        "file_checksum",
        "uploaded_by",
        "review_status",
        "reviewed_by",
        "reviewed_at",
        "rejection_reason",
        "processing_status",
        "processing_started_at",
        "processing_completed_at",
        "processing_error",
        "extracted_text",
        "page_count",
        "chunk_count",
        "is_active",
        "created_at",
        "updated_at",
    ]

    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = [
        "document_version",
        "chunk_index",
        "page_number",
        "created_at",
    ]

    search_fields = [
        "document_version__document__title",
        "content",
    ]

    list_select_related = [
        "document_version",
        "document_version__document",
    ]

    readonly_fields = [
        "document_version",
        "chunk_index",
        "content",
        "page_number",
        "character_start",
        "character_end",
        "metadata",
        "is_active",
        "created_at",
        "updated_at",
    ]

    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False