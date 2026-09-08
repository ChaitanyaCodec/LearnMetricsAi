from django.urls import path

from . import views

app_name = "rag"

urlpatterns = [
    path(
        "ask/",
        views.RagAskAPIView.as_view(),
        name="ask",
    ),
]