from django.http import HttpResponse
from django.views import View


class LoginView(View):
    def get(self, request):
        return HttpResponse("Login Page")


class LogoutView(View):
    def get(self, request):
        return HttpResponse("Logout Page")


class ProfileView(View):
    def get(self, request):
        return HttpResponse("Profile Page")


class PasswordChangeView(View):
    def get(self, request):
        return HttpResponse("Password Change Page")


class PasswordResetView(View):
    def get(self, request):
        return HttpResponse("Password Reset Page")