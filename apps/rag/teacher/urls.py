from django.urls import path

from .document_views import (
    TeacherDocumentExportAPIView,
    TeacherDocumentGenerateAPIView,
    TeacherDocumentGenerationPageView,
)
from .views import TeacherRAGChatView

app_name = "teacher"

urlpatterns = [
    path("", TeacherRAGChatView.as_view(), name="chat"),
    path("documents/", TeacherDocumentGenerationPageView.as_view(), name="documents"),
    path("documents/generate/", TeacherDocumentGenerateAPIView.as_view(), name="document-generate"),
    path("documents/export/<str:file_format>/", TeacherDocumentExportAPIView.as_view(), name="document-export"),
]
