import json
from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.academics.models import (
    Course,
    Department,
    Institution,
    Semester,
    Subject,
)
from apps.rag.models import Conversation
from apps.students.models import Student, StudentEnrollment
from apps.teachers.models import Teacher, TeachingAssignment


class ConversationAccessRevocationAPITests(TestCase):
    """A conversation owner must retain current access to its subject."""

    def setUp(self):
        institution = Institution.objects.create(
            name="Access Institution",
            short_name="ACCESS",
            email="access@example.com",
            phone_number="9876543210",
        )
        department = Department.objects.create(
            institution=institution,
            name="Computer Science",
            code="CSE",
        )
        self.course = Course.objects.create(
            department=department,
            name="Computer Science",
            code="CS",
            duration=3,
        )
        self.semester = Semester.objects.create(
            course=self.course,
            semester_number=1,
            name="Semester 1",
        )
        self.subject = Subject.objects.create(
            semester=self.semester,
            code="CS101",
            name="Computer Science Fundamentals",
        )

        self.teacher_user = User.objects.create_user(
            email="teacher-access@example.com",
            password="test-password",
            role=User.Roles.TEACHER,
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_id="T-ACCESS-1",
        )
        self.assignment = TeachingAssignment.objects.create(
            teacher=self.teacher,
            course=self.course,
            semester=self.semester,
            subject=self.subject,
        )

        self.client.force_login(self.teacher_user)

    def create_conversation(self, user=None):
        return Conversation.objects.create(
            user=user or self.teacher_user,
            subject=self.subject,
            title="Protected conversation",
        )

    def detail_url(self, conversation):
        return reverse(
            "rag:conversation-detail",
            kwargs={"conversation_id": conversation.id},
        )

    def test_revoked_teacher_assignment_hides_conversation_from_list(self):
        self.create_conversation()
        self.assignment.is_active = False
        self.assignment.save(update_fields=["is_active"])

        response = self.client.get(
            reverse("rag:conversation-list-create")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["conversations"], [])

    def test_revoked_teacher_assignment_blocks_conversation_detail(self):
        conversation = self.create_conversation()
        self.assignment.is_active = False
        self.assignment.save(update_fields=["is_active"])

        response = self.client.get(self.detail_url(conversation))

        self.assertEqual(response.status_code, 403)

    def test_revoked_teacher_assignment_blocks_rename(self):
        conversation = self.create_conversation()
        self.assignment.is_active = False
        self.assignment.save(update_fields=["is_active"])

        response = self.client.patch(
            self.detail_url(conversation),
            data=json.dumps({"title": "Unauthorized rename"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        conversation.refresh_from_db()
        self.assertEqual(conversation.title, "Protected conversation")

    def test_revoked_teacher_assignment_blocks_delete(self):
        conversation = self.create_conversation()
        self.assignment.is_active = False
        self.assignment.save(update_fields=["is_active"])

        response = self.client.delete(self.detail_url(conversation))

        self.assertEqual(response.status_code, 403)
        conversation.refresh_from_db()
        self.assertTrue(conversation.is_active)

    def test_revoked_student_enrollment_blocks_conversation_detail(self):
        student_user = User.objects.create_user(
            email="student-access@example.com",
            password="test-password",
            role=User.Roles.STUDENT,
        )
        student = Student.objects.create(
            user=student_user,
            student_id="S-ACCESS-1",
        )
        enrollment = StudentEnrollment.objects.create(
            student=student,
            course=self.course,
            semester=self.semester,
            academic_year="2026-2027",
            roll_number="CS-001",
            enrollment_date=date(2026, 7, 1),
            status=StudentEnrollment.Status.ACTIVE,
        )
        conversation = self.create_conversation(user=student_user)
        self.client.force_login(student_user)

        enrollment.is_active = False
        enrollment.save(update_fields=["is_active"])

        response = self.client.get(self.detail_url(conversation))

        self.assertEqual(response.status_code, 403)
