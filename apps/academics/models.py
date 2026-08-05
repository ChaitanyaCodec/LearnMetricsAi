from django.db import models

from apps.core.models import BaseModel


class Institution(BaseModel):
    """
    Represents the educational institution.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    short_name = models.CharField(
        max_length=50,
        unique=True,
    )

    email = models.EmailField()

    phone_number = models.CharField(
        max_length=20,
    )

    website = models.URLField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    class Meta:
        verbose_name = "Institution"
        verbose_name_plural = "Institutions"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name



class Department(BaseModel):
    """
    Represents an academic department within an institution.
    """

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="departments",
        help_text="Institution to which this department belongs.",
    )

    name = models.CharField(
        max_length=150,
        help_text="Department name.",
    )

    code = models.CharField(
        max_length=20,
        help_text="Unique department code within an institution.",
    )

    description = models.TextField(
        blank=True,
        help_text="Optional department description.",
    )

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_department_name_per_institution",
            ),
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="unique_department_code_per_institution",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Course(BaseModel):
    """
    Represents an academic course/program offered
    by a department.
    """

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="courses",
        help_text="Department offering this course.",
    )

    name = models.CharField(
        max_length=150,
        help_text="Course name.",
    )

    code = models.CharField(
        max_length=20,
        help_text="Unique course code within a department.",
    )

    duration = models.PositiveSmallIntegerField(
        help_text="Course duration in years.",
    )

    description = models.TextField(
        blank=True,
        help_text="Optional course description.",
    )

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="unique_course_name_per_department",
            ),
            models.UniqueConstraint(
                fields=["department", "code"],
                name="unique_course_code_per_department",
            ),
        ]

    def __str__(self) -> str:
        return self.name

class Semester(BaseModel):
    """
    Represents a semester within an academic course.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="semesters",
        help_text="Course to which this semester belongs.",
    )

    semester_number = models.PositiveSmallIntegerField(
        help_text="Semester number (e.g. 1, 2, 3...).",
    )

    name = models.CharField(
        max_length=50,
        help_text="Semester name.",
    )

    class Meta:
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"
        ordering = ["course", "semester_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["course", "semester_number"],
                name="unique_semester_per_course",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.course.name} - Semester {self.semester_number}"

class Subject(BaseModel):
    """
    Represents an academic subject offered
    within a semester.
    """

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="subjects",
        help_text="Semester to which this subject belongs.",
    )

    code = models.CharField(
        max_length=20,
        help_text="Subject code.",
    )

    name = models.CharField(
        max_length=200,
        help_text="Subject name.",
    )

    credits = models.PositiveSmallIntegerField(
        default=4,
        help_text="Academic credits assigned to this subject.",
    )

    description = models.TextField(
        blank=True,
        help_text="Optional subject description.",
    )

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["semester", "code"],
                name="unique_subject_code_per_semester",
            ),
            models.UniqueConstraint(
                fields=["semester", "name"],
                name="unique_subject_name_per_semester",
            ),
        ]

    def __str__(self) -> str:
        return self.name