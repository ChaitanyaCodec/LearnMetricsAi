from django import forms

from .models import (
    Institution,
    Department,
    Course,
    Semester,
    Subject,
)

#-------------------------------
#     Institution Forms 
#-------------------------------

class InstitutionForm(forms.ModelForm):
    """
    Form for creating and updating institutions.
    """

    class Meta:
        model = Institution

        fields = (
            "name",
            "short_name",
            "email",
            "phone_number",
            "website",
            "address",
            "is_active",
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Institution Name",
                }
            ),
            "short_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Short Name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Email Address",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone Number",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Website",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Address",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

#-------------------------------
#Department Forms
#-------------------------------
class DepartmentForm(forms.ModelForm):
    """
    Form for creating and updating departments.
    """

    class Meta:
        model = Department

        fields = (
            "institution",
            "name",
            "code",
            "description",
            "is_active",
        )

        widgets = {
            "institution": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Department Name",
                }
            ),
            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Department Code",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Department Description",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

# ==========================================================
# Course Form
# ==========================================================

class CourseForm(forms.ModelForm):
    """
    Form for creating and updating courses.
    """

    class Meta:
        model = Course

        fields = (
            "department",
            "name",
            "code",
            "duration",
            "description",
            "is_active",
        )

        widgets = {

            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Course Name",
                }
            ),

            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Course Code",
                }
            ),

            "duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Duration (Years)",
                    "min": 1,
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Course Description",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

# ==========================================================
# Semester Form
# ==========================================================

class SemesterForm(forms.ModelForm):
    """
    Form for creating and updating semesters.
    """

    class Meta:
        model = Semester

        fields = [
            "course",
            "semester_number",
            "name",
            "is_active",
        ]

        widgets = {
            "course": forms.Select(
                attrs={"class": "form-select"}
            ),
            "semester_number": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Semester Name",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

# ==========================================================
# Subject Form
# ==========================================================
class SubjectForm(forms.ModelForm):
    """
    Form for creating and updating subjects.
    """

    class Meta:
        model = Subject

        fields = [
            "semester",
            "code",
            "name",
            "credits",
            "description",
            "is_active",
        ]

        widgets = {
            "semester": forms.Select(
                attrs={"class": "form-select"}
            ),
            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Subject Code",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Subject Name",
                }
            ),
            "credits": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Description",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }