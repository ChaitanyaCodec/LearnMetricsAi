from django.urls import reverse

from .models import User


class AuthenticationService:
    """
    Handles authentication-related business logic.
    """

    @staticmethod
    def get_login_redirect(user: User) -> str:
        """
        Returns the dashboard URL based on the user's role.
        """

        role_redirects = {
            User.Roles.ADMIN: "dashboard:admin",
            User.Roles.TEACHER: "dashboard:teacher",
            User.Roles.STUDENT: "dashboard:student",
        }

        return reverse(
            role_redirects.get(
                user.role,
                "dashboard:student",
            )
        )

class ProfileService:
    """User profile business logic."""
    pass


class PasswordService:
    """Password management business logic."""
    pass