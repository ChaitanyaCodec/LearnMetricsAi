import json
from unittest.mock import Mock

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.academics.models import Course, Department, Institution, Semester, Subject
from apps.documents.models import Document, DocumentChunk, DocumentVersion
from apps.rag.teacher.document_generation import (
    TeacherDocumentGenerationError,
    TeacherDocumentGenerationService,
    TeacherDocumentSourceService,
)
from apps.teachers.models import Teacher, TeachingAssignment


class TeacherDocumentGenerationTests(TestCase):
    def setUp(self):
        institution = Institution.objects.create(
            name="Generation Institution", short_name="GEN",
            email="gen@example.com", phone_number="9876543210",
        )
        department = Department.objects.create(
            institution=institution, name="Computer Science", code="CSGEN",
        )
        course = Course.objects.create(
            department=department, name="MCA", code="MCAGEN", duration=2,
        )
        semester = Semester.objects.create(
            course=course, semester_number=1, name="Semester 1",
        )
        self.subject = Subject.objects.create(
            semester=semester, code="DBGEN", name="Database Systems",
        )
        self.teacher_user = User.objects.create_user(
            email="teacher-gen@example.com", password="test-password",
            role=User.Roles.TEACHER,
        )
        teacher_profile = Teacher.objects.create(
            user=self.teacher_user, employee_id="T-GEN-01",
        )
        TeachingAssignment.objects.create(
            teacher=teacher_profile, course=course, semester=semester,
            subject=self.subject, is_active=True,
        )
        self.provider = Mock()
        self.provider.generate.return_value = "# Lesson Plan\n\n## Objectives\n- Understand normalization"

    def test_teacher_can_generate_from_instructions_without_sources(self):
        service = TeacherDocumentGenerationService(provider=self.provider)
        result = service.generate(
            user=self.teacher_user,
            subject_id=self.subject.pk,
            instructions="Create a lesson plan on normalization.",
            source_document_ids=[],
        )
        self.assertEqual(result["subject_name"], "Database Systems")
        self.assertIn("Lesson Plan", result["content"])
        self.assertEqual(result["source_titles"], [])
        prompt = self.provider.generate.call_args.args[0]
        self.assertIn("No source documents were selected", prompt)

    def test_student_cannot_use_generation_service(self):
        student = User.objects.create_user(
            email="student-gen@example.com", password="test-password",
            role=User.Roles.STUDENT,
        )
        service = TeacherDocumentGenerationService(provider=self.provider)
        with self.assertRaises(TeacherDocumentGenerationError):
            service.generate(
                user=student, subject_id=self.subject.pk,
                instructions="Create notes", source_document_ids=[],
            )
        self.provider.generate.assert_not_called()

    def test_teacher_cannot_generate_for_unassigned_subject(self):
        other_subject = Subject.objects.create(
            semester=self.subject.semester, code="OTHERGEN", name="Other Subject",
        )
        service = TeacherDocumentGenerationService(provider=self.provider)
        with self.assertRaises(TeacherDocumentGenerationError):
            service.generate(
                user=self.teacher_user, subject_id=other_subject.pk,
                instructions="Create notes", source_document_ids=[],
            )
        self.provider.generate.assert_not_called()

    def test_unpublished_document_cannot_be_used_as_source(self):
        document = Document.objects.create(
            title="Draft source", subject=self.subject,
            status=Document.Status.DRAFT, created_by=self.teacher_user,
        )
        service = TeacherDocumentGenerationService(provider=self.provider)
        with self.assertRaises(TeacherDocumentGenerationError):
            service.generate(
                user=self.teacher_user, subject_id=self.subject.pk,
                instructions="Create notes from this source",
                source_document_ids=[document.pk],
            )
        self.provider.generate.assert_not_called()

    def test_source_list_only_returns_approved_published_processed_documents(self):
        draft = Document.objects.create(
            title="Draft source", subject=self.subject,
            status=Document.Status.DRAFT, created_by=self.teacher_user,
        )
        documents = TeacherDocumentSourceService.for_teacher(self.teacher_user)
        self.assertNotIn(draft.pk, list(documents.values_list("pk", flat=True)))

    def test_approved_published_source_is_used_as_reference_context(self):
        document = Document.objects.create(
            title="Published source", subject=self.subject,
            status=Document.Status.APPROVED, created_by=self.teacher_user,
        )
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            source_file="documents/test/source.txt",
            original_filename="source.txt",
            uploaded_by=self.teacher_user,
            review_status=DocumentVersion.ReviewStatus.APPROVED,
            processing_status=DocumentVersion.ProcessingStatus.COMPLETED,
            extracted_text="Normalization reduces data redundancy.",
        )
        document.published_version = version
        document.save(update_fields=["published_version"])
        DocumentChunk.objects.create(
            document_version=version,
            chunk_index=0,
            content="Normalization reduces data redundancy.",
            page_number=2,
        )

        service = TeacherDocumentGenerationService(provider=self.provider)
        result = service.generate(
            user=self.teacher_user,
            subject_id=self.subject.pk,
            instructions="Create revision notes about normalization.",
            source_document_ids=[document.pk],
        )
        prompt = self.provider.generate.call_args.args[0]
        self.assertIn("Normalization reduces data redundancy.", prompt)
        self.assertIn("Published source", prompt)
        self.assertEqual(result["source_titles"], ["Published source"])

    def test_student_is_denied_generation_page_and_api(self):
        student = User.objects.create_user(
            email="student-page@example.com", password="test-password",
            role=User.Roles.STUDENT,
        )
        self.client.force_login(student)
        page_response = self.client.get(reverse("rag:teacher:documents"))
        self.assertEqual(page_response.status_code, 403)
        api_response = self.client.post(
            reverse("rag:teacher:document-generate"),
            data=json.dumps({
                "subject_id": self.subject.pk,
                "instructions": "Create notes",
                "source_document_ids": [],
            }),
            content_type="application/json",
        )
        self.assertEqual(api_response.status_code, 403)

    def test_teacher_document_page_is_available_to_assigned_teacher(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse("rag:teacher:documents"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Document Studio")


class TeacherDocumentExportAuthorizationTests(TestCase):
    def test_student_cannot_export(self):
        student = User.objects.create_user(
            email="student-export@example.com", password="test-password",
            role=User.Roles.STUDENT,
        )
        self.client.force_login(student)
        response = self.client.post(
            reverse("rag:teacher:document-export", kwargs={"file_format": "docx"}),
            data=json.dumps({"content": "# Draft"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)


class TeacherDocumentExporterTests(TestCase):
    def test_all_supported_formats_return_download_responses(self):
        from apps.rag.teacher.exporters import export_document

        expected_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
        for file_format, content_type in expected_types.items():
            with self.subTest(file_format=file_format):
                response = export_document(
                    "# Lesson Plan\n\n## Objectives\n- Explain the topic",
                    file_format,
                    filename=f"lesson-plan.{file_format}",
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], content_type)
                self.assertIn(f"lesson-plan.{file_format}", response["Content-Disposition"])
                self.assertEqual(response["Cache-Control"], "no-store, private")
                self.assertGreater(len(response.content), 100)

    def test_unsupported_format_is_rejected(self):
        from apps.rag.teacher.exporters import export_document

        with self.assertRaises(ValueError):
            export_document("# Draft", "html")
