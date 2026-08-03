from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View

from .forms import LoginForm
from .services import AuthenticationService


class LoginView(DjangoLoginView):

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Redirect users based on their role.
        """
        return AuthenticationService.get_login_redirect(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().full_name}!")
        return super().form_valid(form)


class LogoutView(DjangoLogoutView):

    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            messages.success(request, "You have been logged out successfully.")

        return super().dispatch(request, *args, **kwargs)


# class ProfileView(View):
#     def get(self, request):
#         return HttpResponse("Profile Page")


# class PasswordChangeView(View):
#     def get(self, request):
#         return HttpResponse("Password Change Page")


# class PasswordResetView(View):
#     def get(self, request):
#         return HttpResponse("Password Reset Page")
