from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password",
            }
        ),
    )


# class ProfileUpdateForm(forms.Form):
#     pass


# class CustomPasswordChangeForm(forms.Form):
#     pass