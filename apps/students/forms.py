from django import forms

from apps.accounts.models import User
from apps.academics.models import Course, Semester

from .models import Student, StudentEnrollment


class StudentForm(forms.ModelForm):
    """
    Form for creating and updating Student profiles.
    """

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email Address",
            }
        ),
    )

    first_name = forms.CharField(
        label="First Name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First Name",
            }
        ),
    )

    last_name = forms.CharField(
        label="Last Name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name",
            }
        ),
    )

    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone Number",
            }
        ),
    )

    class Meta:
        model = Student

        fields = (
            "student_id",
            "admission_date",
        )

        widgets = {
            "student_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Student ID",
                }
            ),
            "admission_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:

            self.fields["email"].initial = (
                self.instance.user.email
            )

            self.fields["first_name"].initial = (
                self.instance.user.first_name
            )

            self.fields["last_name"].initial = (
                self.instance.user.last_name
            )

            self.fields["phone_number"].initial = (
                self.instance.user.phone_number
            )


class StudentCreateForm(StudentForm):
    """
    Form used when Admin creates a new Student.
    """

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        ),
    )

    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm Password",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(
            email=email
        ).exists():

            raise forms.ValidationError(
                "A user with this email already exists."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get(
            "password_confirm"
        )

        if (
            password
            and password_confirm
            and password != password_confirm
        ):
            self.add_error(
                "password_confirm",
                "Passwords do not match.",
            )

        return cleaned_data


class StudentEnrollmentForm(forms.ModelForm):
    """
    Form for creating and updating student enrollments.
    """

    class Meta:
        model = StudentEnrollment

        fields = (
            "student",
            "course",
            "semester",
            "academic_year",
            "roll_number",
            "enrollment_date",
            "status",
        )

        widgets = {
            "student": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "course": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "semester": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "academic_year": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "2026-27",
                }
            ),
            "roll_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Roll Number",
                }
            ),
            "enrollment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        course = cleaned_data.get("course")
        semester = cleaned_data.get("semester")

        if (
            course
            and semester
            and semester.course_id != course.pk
        ):
            self.add_error(
                "semester",
                "Selected semester does not belong "
                "to the selected course.",
            )

        return cleaned_data