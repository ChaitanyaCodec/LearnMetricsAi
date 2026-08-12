from django.conf import settings
from django.db import models

from apps.academics.models import Course, Semester
from apps.core.models import BaseModel


class Student(BaseModel):
    """
    Domain profile for a user whose role is STUDENT.

    Authentication and common identity information are
    maintained by the accounts.User model.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    student_id = models.CharField(
        max_length=50,
        unique=True,
    )

    admission_date = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["student_id"]
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return f"{self.student_id} - {self.user.full_name}"


class StudentEnrollment(BaseModel):
    """
    Represents a student's academic enrollment.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        DROPPED = "DROPPED", "Dropped"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="student_enrollments",
    )

    semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        related_name="student_enrollments",
    )

    academic_year = models.CharField(
        max_length=20,
    )

    roll_number = models.CharField(
        max_length=50,
    )

    enrollment_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = [
            "-academic_year",
            "roll_number",
        ]

        verbose_name = "Student Enrollment"
        verbose_name_plural = "Student Enrollments"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "academic_year",
                ],
                name="unique_student_academic_year",
            ),
            models.UniqueConstraint(
                fields=[
                    "course",
                    "academic_year",
                    "roll_number",
                ],
                name="unique_roll_number_per_course_year",
            ),
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.course} - "
            f"{self.academic_year}"
        )