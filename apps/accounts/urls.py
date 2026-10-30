from django.urls import path

from .admin_password_reset import AdminPasswordResetView

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "admin/password-reset/<str:kind>/<int:pk>/",
        AdminPasswordResetView.as_view(),
        name="admin-password-reset",
    ),
    path(
        "login/",
        views.LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        views.LogoutView.as_view(),
        name="logout",
    ),
    # path(
    #     "profile/",
    #     views.ProfileView.as_view(),
    #     name="profile",
    # ),
    # path(
    #     "password/change/",
    #     views.PasswordChangeView.as_view(),
    #     name="password_change",
    # ),
    # path(
    #     "password/reset/",
    #     views.PasswordResetView.as_view(),
    #     name="password_reset",
    # ),
]
