from apps.students.models import Student, StudentEnrollment
from apps.teachers.models import Teacher, TeachingAssignment

from django.test import TestCase

from apps.accounts.models import User
from apps.academics.models import (
    Course,
    Department,
    Institution,
    Semester,
    Subject,
)
from apps.rag.conversations import can_access_conversation_subject


class ConversationPermissionTests(TestCase):
    def setUp(self):
        institution = Institution.objects.create(
            name="Permission Institution",
            short_name="PI",
            email="permission@example.com",
            phone_number="9876543210",
        )

        department = Department.objects.create(
            institution=institution,
            name="Computer Science",
            code="CSE",
        )

        course = Course.objects.create(
            department=department,
            name="B.Sc. Computer Science",
            code="BSC-CS",
            duration=3,
        )

        semester = Semester.objects.create(
            course=course,
            semester_number=1,
            name="Semester 1",
        )

        self.subject = Subject.objects.create(
            semester=semester,
            code="DBMS101",
            name="Database Management Systems",
        )

    def test_unauthenticated_user_is_denied(self):
        user = User.objects.create_user(
            email="inactive@example.com",
            password="test-password",
        )

        user.is_active = False
        user.save(update_fields=["is_active"])

        self.assertFalse(
            can_access_conversation_subject(
                user,
                self.subject,
            )
        )

    def test_admin_is_allowed(self):
        user = User.objects.create_user(
            email="admin@example.com",
            password="test-password",
            role=User.Roles.ADMIN,
        )

        self.assertTrue(
            can_access_conversation_subject(
                user,
                self.subject,
            )
        )

    def test_regular_user_is_denied(self):
        user = User.objects.create_user(
            email="regular@example.com",
            password="test-password",
        )

        self.assertFalse(
            can_access_conversation_subject(
                user,
                self.subject,
            )
        )
    def test_teacher_with_active_assignment_is_allowed(self):
        user = User.objects.create_user(
            email="teacher@example.com",
            password="test-password",
            role=User.Roles.TEACHER,
        )

        teacher = Teacher.objects.create(
            user=user,
            employee_id="T001",
        )

        TeachingAssignment.objects.create(
            teacher=teacher,
            course=self.subject.semester.course,
            semester=self.subject.semester,
            subject=self.subject,
            is_active=True,
        )

        self.assertTrue(
            can_access_conversation_subject(
                user,
                self.subject,
            )
        )

    def test_teacher_with_inactive_assignment_is_denied(self):
        user = User.objects.create_user(
            email="inactive-teacher@example.com",
            password="test-password",
            role=User.Roles.TEACHER,
        )

        teacher = Teacher.objects.create(
            user=user,
            employee_id="T002",
        )

        TeachingAssignment.objects.create(
            teacher=teacher,
            course=self.subject.semester.course,
            semester=self.subject.semester,
            subject=self.subject,
            is_active=False,
        )

        self.assertFalse(
            can_access_conversation_subject(
                user,
                self.subject,
            )
        )

    def test_student_with_active_enrollment_is_allowed(self):
        user = User.objects.create_user(
            email="student@example.com",
            password="test-password",
            role=User.Roles.STUDENT,
        )

        student = Student.objects.create(
            user=user,
            student_id="S001",
        )

        StudentEnrollment.objects.create(
            student=student,
            course=self.subject.semester.course,
            semester=self.subject.semester,
            academic_year="2026-27",
            roll_number="R001",
            enrollment_date="2026-06-01",
            status=StudentEnrollment.Status.ACTIVE,
            is_active=True,
        )

        self.assertTrue(
            can_access_conversation_subject(
                user,
                self.subject,
            )
        )

    def test_student_with_inactive_enrollment_is_denied(self):
        user = User.objects.create_user(
            email="inactive-student@example.com",
            password="test-password",
            role=User.Roles.STUDENT,
        )

        student = Student.objects.create(
            user=user,
            student_id="S002",
        )

        StudentEnrollment.objects.create(
            student=student,
            course=self.subject.semester.course,
            semester=self.subject.semester,
            academic_year="2026-27",
            roll_number="R002",
            enrollment_date="2026-06-01",
            status=StudentEnrollment.Status.ACTIVE,
            is_active=False,
        )

        self.assertFalse(
            can_access_conversation_subject(
                user,
                self.subject,
            )
        )