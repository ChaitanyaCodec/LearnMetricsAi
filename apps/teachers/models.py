from django.conf import settings
from django.db import models

from apps.academics.models import Course, Semester, Subject
from apps.core.models import BaseModel


class Teacher(BaseModel):
    """
    Domain profile for a user whose role is TEACHER.

    Authentication and common identity information remain
    in the accounts.User model.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
    )

    employee_id = models.CharField(
        max_length=50,
        unique=True,
    )

    joining_date = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["employee_id"]
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

    def __str__(self):
        return f"{self.employee_id} - {self.user.full_name}"


class TeachingAssignment(BaseModel):
    """
    Represents a subject assigned to a teacher
    for a specific course and semester.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="teaching_assignments",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )

    semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )

    class Meta:
        ordering = [
            "course",
            "semester",
            "subject",
            "teacher",
        ]

        verbose_name = "Teaching Assignment"
        verbose_name_plural = "Teaching Assignments"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "teacher",
                    "course",
                    "semester",
                    "subject",
                ],
                name="unique_teacher_assignment",
            ),
        ]

    def __str__(self):
        return (
            f"{self.teacher} - "
            f"{self.course} - "
            f"{self.subject}"
        )