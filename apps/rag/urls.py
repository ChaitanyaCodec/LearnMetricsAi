from django.urls import include , path

from . import views

app_name = "rag"

urlpatterns = [
    path(
        "ask/",
        views.RagAskAPIView.as_view(),
        name="ask",
    ),
    path(
        "conversations/",
        views.ConversationListCreateAPIView.as_view(),
        name="conversation-list-create",
    ),
    path(
        "conversations/<uuid:conversation_id>/",
        views.ConversationDetailAPIView.as_view(),
        name="conversation-detail",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        views.ConversationMessageAPIView.as_view(),
        name="conversation-message",
    ),
]