from datetime import date

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.accounts.models import User
from apps.academics.models import (
    Course,
    Department,
    Institution,
    Semester,
    Subject,
)
from apps.students.models import (
    Student,
    StudentEnrollment,
)
from apps.teachers.models import (
    Teacher,
    TeachingAssignment,
)
from apps.documents.models import (
    Document,
    DocumentVersion,
)
from apps.documents.permissions import (
    can_view_document,
)
from apps.documents.services import (
    approve_document_version,
    create_document_with_initial_version,
    submit_latest_version_for_review,
    upload_new_document_version,
)


class DocumentServiceTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(
            name="LearnMetrics University",
            short_name="LMU",
            email="admin@lmu.test",
            phone_number="1234567890",
        )

        self.department = Department.objects.create(
            institution=self.institution,
            name="Computer Science",
            code="CS",
        )

        self.course = Course.objects.create(
            department=self.department,
            name="B.Tech Computer Science",
            code="BTCS",
            duration=4,
        )

        self.semester = Semester.objects.create(
            course=self.course,
            semester_number=1,
            name="Semester 1",
        )

        self.subject = Subject.objects.create(
            semester=self.semester,
            code="CS101",
            name="Introduction to Computing",
        )

        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            role=User.Roles.ADMIN,
        )

        self.teacher_user = User.objects.create_user(
            email="teacher@test.com",
            password="password123",
            first_name="Teacher",
            last_name="User",
            role=User.Roles.TEACHER,
        )

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_id="EMP001",
        )

        TeachingAssignment.objects.create(
            teacher=self.teacher,
            course=self.course,
            semester=self.semester,
            subject=self.subject,
        )

        self.student_user = User.objects.create_user(
            email="student@test.com",
            password="password123",
            first_name="Student",
            last_name="User",
            role=User.Roles.STUDENT,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            student_id="STU001",
        )

        StudentEnrollment.objects.create(
            student=self.student,
            course=self.course,
            semester=self.semester,
            academic_year="2026-2027",
            roll_number="001",
            enrollment_date=date.today(),
            status=StudentEnrollment.Status.ACTIVE,
        )

    def tearDown(self):
        for version in DocumentVersion.objects.all():
            version.source_file.delete(save=False)

    def make_text_file(self, name="notes.txt"):
        return SimpleUploadedFile(
            name,
            b"Introduction to computing.\n"
            b"This is a document used for testing.",
            content_type="text/plain",
        )

    def mark_processing_completed(self, version):
        version.processing_status = (
            DocumentVersion.ProcessingStatus.COMPLETED
        )
        version.save(
            update_fields=[
                "processing_status",
                "updated_at",
            ]
        )

    def create_document(self):
        return create_document_with_initial_version(
            user=self.teacher_user,
            title="Week 1 Notes",
            description="Introduction notes",
            subject=self.subject,
            source_file=self.make_text_file(),
        )

    def test_teacher_can_create_document_for_assigned_subject(self):
        version = self.create_document()

        self.assertEqual(version.version_number, 1)
        self.assertEqual(
            version.document.created_by,
            self.teacher_user,
        )
        self.assertEqual(
            version.document.status,
            Document.Status.DRAFT,
        )

    def test_invalid_extension_is_rejected(self):
        invalid_file = SimpleUploadedFile(
            "malware.exe",
            b"not a document",
            content_type="application/octet-stream",
        )

        with self.assertRaises(ValidationError):
            create_document_with_initial_version(
                user=self.teacher_user,
                title="Invalid file",
                description="",
                subject=self.subject,
                source_file=invalid_file,
            )

    def test_admin_approval_publishes_processed_version(self):
        version = self.create_document()
        self.mark_processing_completed(version)

        submit_latest_version_for_review(
            user=self.teacher_user,
            document_id=version.document_id,
        )

        approve_document_version(
            user=self.admin_user,
            document_version_id=version.id,
        )

        version.refresh_from_db()
        document = Document.objects.get(
            pk=version.document_id
        )

        self.assertEqual(
            version.review_status,
            DocumentVersion.ReviewStatus.APPROVED,
        )
        self.assertEqual(
            document.published_version_id,
            version.id,
        )
        self.assertEqual(
            document.status,
            Document.Status.APPROVED,
        )

    def test_new_pending_version_does_not_replace_published_version(self):
        first_version = self.create_document()
        self.mark_processing_completed(first_version)

        submit_latest_version_for_review(
            user=self.teacher_user,
            document_id=first_version.document_id,
        )

        approve_document_version(
            user=self.admin_user,
            document_version_id=first_version.id,
        )

        second_version = upload_new_document_version(
            user=self.teacher_user,
            document_id=first_version.document_id,
            source_file=self.make_text_file("notes-v2.txt"),
        )
        self.mark_processing_completed(second_version)

        second_version = submit_latest_version_for_review(
            user=self.teacher_user,
            document_id=first_version.document_id,
        )

        document = Document.objects.get(
            pk=first_version.document_id
        )

        self.assertEqual(
            second_version.review_status,
            DocumentVersion.ReviewStatus.PENDING_REVIEW,
        )
        self.assertEqual(
            document.published_version_id,
            first_version.id,
        )
    def test_active_student_can_view_published_document(self):
        version = self.create_document()
        self.mark_processing_completed(version)

        submit_latest_version_for_review(
            user=self.teacher_user,
            document_id=version.document_id,
        )

        approve_document_version(
            user=self.admin_user,
            document_version_id=version.id,
        )

        document = Document.objects.get(
            pk=version.document_id
        )

        self.assertTrue(
            can_view_document(
                self.student_user,
                document,
            )
        )

def test_submitted_version_appears_in_admin_review_queue(self):
    version = self.create_document()
    self.mark_processing_completed(version)

    submit_latest_version_for_review(
        user=self.teacher_user,
        document_id=version.document_id,
    )

    queued_versions = get_admin_review_queue()

    self.assertTrue(
        queued_versions.filter(pk=version.id).exists()
    )

    version.refresh_from_db()

    self.assertEqual(
        version.review_status,
        DocumentVersion.ReviewStatus.PENDING_REVIEW,
    )