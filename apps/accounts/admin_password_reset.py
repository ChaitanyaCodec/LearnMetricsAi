"""Administrator-assisted password reset for student and teacher accounts."""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.mixins import AdminRequiredMixin
from apps.students.models import Student
from apps.teachers.models import Teacher

User = get_user_model()


class AdminPasswordResetView(AdminRequiredMixin, View):
    """Let administrators set a new password without revealing the old one."""
    template_name = "accounts/admin_password_reset.html"
    profile_models = {"student": Student, "teacher": Teacher}
    list_routes = {"student": "students:student-list", "teacher": "teachers:teacher-list"}

    def _profile(self, kind, pk):
        model = self.profile_models.get(kind)
        if model is None:
            from django.http import Http404
            raise Http404("Unsupported account type.")
        return get_object_or_404(model.objects.select_related("user"), pk=pk)

    def get(self, request, kind, pk):
        profile = self._profile(kind, pk)
        return render(request, self.template_name, {"profile": profile, "kind": kind})

    def post(self, request, kind, pk):
        profile = self._profile(kind, pk)
        password = request.POST.get("password", "")
        confirmation = request.POST.get("confirm_password", "")
        context = {"profile": profile, "kind": kind}

        if not password:
            messages.error(request, "Enter a new password.")
        elif password != confirmation:
            messages.error(request, "The passwords do not match.")
        else:
            try:
                validate_password(password, user=profile.user)
            except ValidationError as exc:
                for error in exc.messages:
                    messages.error(request, error)
            else:
                profile.user.set_password(password)
                profile.user.save(update_fields=["password"])
                messages.success(request, f"Password reset successfully for {profile.user.full_name}. Ask them to sign in with the new password.")
                return redirect(self.list_routes[kind])

        return render(request, self.template_name, context, status=400)
