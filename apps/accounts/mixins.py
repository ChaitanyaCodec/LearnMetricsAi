from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from .models import User


class RoleRequiredMixin(AccessMixin):

    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return self.handle_no_permission()
        print("AUTH USER:", request.user)
        print("AUTH EMAIL:", request.user.email)
        print("AUTH ROLE:", repr(request.user.role))
        print("ALLOWED ROLES:", repr(self.allowed_roles))


        if request.user.role not in self.allowed_roles:
            raise PermissionDenied("You do not have permission to access this page.")
        

        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = [User.Roles.ADMIN]


class TeacherRequiredMixin(RoleRequiredMixin):
    allowed_roles = [User.Roles.TEACHER]


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = [User.Roles.STUDENT]


class TeacherOrAdminMixin(RoleRequiredMixin):
    allowed_roles = [
        User.Roles.ADMIN,
        User.Roles.TEACHER,
    ]
