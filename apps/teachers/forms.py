from django import forms

from apps.accounts.models import User
from apps.academics.models import Course, Semester, Subject

from .models import Teacher, TeachingAssignment


class TeacherForm(forms.ModelForm):
    """
    Form for updating an existing Teacher profile.
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
        model = Teacher

        fields = (
            "employee_id",
            "joining_date",
        )

        widgets = {
            "employee_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Employee ID",
                }
            ),
            "joining_date": forms.DateInput(
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

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(
            email=email
        ).exclude(
            pk=self.instance.user.pk
        ).exists():
            raise forms.ValidationError(
                "A user with this email already exists."
            )

        return email


class TeacherCreateForm(TeacherForm):
    """
    Form used when an Administrator creates a Teacher.
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


class TeachingAssignmentForm(forms.ModelForm):
    """
    Form for assigning a Teacher to a Subject
    within a specific Course and Semester.
    """

    class Meta:
        model = TeachingAssignment

        fields = (
            "teacher",
            "course",
            "semester",
            "subject",
        )

        widgets = {
            "teacher": forms.Select(
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
            "subject": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only users with an actual Teacher profile
        # should appear in the assignment dropdown.
        self.fields["teacher"].queryset = (
            Teacher.objects
            .select_related("user")
            .filter(
                user__role=User.Roles.TEACHER,
                user__is_active=True,
            )
            .order_by(
                "employee_id"
            )
        )

        # If the form is submitted, narrow the dependent
        # choices according to the selected values.
        course_id = None
        semester_id = None

        if self.is_bound:

            course_id = self.data.get(
                "course"
            )

            semester_id = self.data.get(
                "semester"
            )

        elif self.instance.pk:

            course_id = self.instance.course_id

            semester_id = self.instance.semester_id


        if course_id:

            self.fields["semester"].queryset = (
                Semester.objects
                .filter(
                    course_id=course_id
                )
                .order_by(
                    "semester_number"
                )
            )

        else:

            self.fields["semester"].queryset = (
                Semester.objects.none()
            )


        if semester_id:

            self.fields["subject"].queryset = (
                Subject.objects
                .filter(
                    semester_id=semester_id
                )
                .order_by(
                    "name"
                )
            )

        else:

            self.fields["subject"].queryset = (
                Subject.objects.none()
            )
    def clean(self):
        cleaned_data = super().clean()

        course = cleaned_data.get("course")
        semester = cleaned_data.get("semester")
        subject = cleaned_data.get("subject")

        if course and semester:

            if semester.course_id != course.pk:
                self.add_error(
                    "semester",
                    "Selected semester does not belong "
                    "to the selected course.",
                )

        if semester and subject:

            if subject.semester_id != semester.pk:
                self.add_error(
                    "subject",
                    "Selected subject does not belong "
                    "to the selected semester.",
                )

        if course and subject:

            if subject.semester.course_id != course.pk:
                self.add_error(
                    "subject",
                    "Selected subject does not belong "
                    "to the selected course.",
                )

        return cleaned_data