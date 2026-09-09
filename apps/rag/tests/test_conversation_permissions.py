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