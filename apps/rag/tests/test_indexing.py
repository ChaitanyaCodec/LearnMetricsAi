from unittest.mock import Mock

from django.test import TestCase

from apps.accounts.models import User
from apps.academics.models import (
    Institution,
    Department,
    Course,
    Semester,
    Subject,
)
from apps.documents.models import (
    Document,
    DocumentChunk,
    DocumentVersion,
)

from apps.rag.indexing import (
    IndexingError,
    index_chunk,
    index_document_version,
)
from apps.rag.models import ChunkEmbedding


class IndexChunkTests(TestCase):
    """Tests for indexing individual document chunks."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="teacher@example.com",
            password="testpassword",
            role=User.Roles.TEACHER,
        )

        institution = Institution.objects.create(
            name="Test Institution",
            short_name="TEST",
            email="test@example.com",
            phone_number="1234567890",
        )

        department = Department.objects.create(
            institution=institution,
            name="Computer Science",
            code="CSE",
        )

        course = Course.objects.create(
            department=department,
            name="Bachelor of Computer Applications",
            code="BCA",
            duration=3,
        )

        semester = Semester.objects.create(
            course=course,
            semester_number=1,
            name="Semester 1",
        )

        self.subject = Subject.objects.create(
            semester=semester,
            code="DBMS",
            name="Database Management Systems",
        )

        self.document = Document.objects.create(
            title="DBMS Notes",
            description="Database management system notes.",
            subject=self.subject,
            created_by=self.user,
            status=Document.Status.APPROVED,
            is_active=True,
        )

        self.version = DocumentVersion.objects.create(
            document=self.document,
            version_number=1,
            source_file="documents/test.pdf",
            original_filename="test.pdf",
            content_type="application/pdf",
            file_size=100,
            file_checksum="test-checksum",
            uploaded_by=self.user,
            review_status=DocumentVersion.ReviewStatus.APPROVED,
            processing_status=DocumentVersion.ProcessingStatus.COMPLETED,
        )

        self.document.published_version = self.version
        self.document.save(update_fields=["published_version"])

        self.chunk = DocumentChunk.objects.create(
            document_version=self.version,
            chunk_index=0,
            content="A database management system stores and manages data.",
        )

    def test_index_chunk_creates_embedding(self):
        embedding_service = Mock()

        embedding_service.embed_text.return_value = [
            0.1
        ] * 384

        result = index_chunk(
            chunk=self.chunk,
            embedding_service=embedding_service,
        )

        self.assertIsInstance(
            result,
            ChunkEmbedding,
        )

        self.assertEqual(
            result.document_chunk,
            self.chunk,
        )

        self.assertEqual(
            result.dimensions,
            384,
        )

        self.assertEqual(
            result.model_name,
            "sentence-transformers/all-MiniLM-L6-v2",
        )

        embedding_service.embed_text.assert_called_once_with(
            self.chunk.content
        )

    def test_index_chunk_is_idempotent(self):
        embedding_service = Mock()

        embedding_service.embed_text.return_value = [
            0.1
        ] * 384

        first = index_chunk(
            chunk=self.chunk,
            embedding_service=embedding_service,
        )

        second = index_chunk(
            chunk=self.chunk,
            embedding_service=embedding_service,
        )

        self.assertEqual(
            first.pk,
            second.pk,
        )

        self.assertEqual(
            ChunkEmbedding.objects.filter(
                document_chunk=self.chunk
            ).count(),
            1,
        )

    def test_invalid_chunk_is_rejected(self):
        with self.assertRaises(IndexingError):
            index_chunk(
                chunk="not-a-document-chunk",
                embedding_service=Mock(),
            )

    def test_empty_chunk_is_rejected(self):
        self.chunk.content = "   "
        self.chunk.save(update_fields=["content"])

        with self.assertRaises(IndexingError):
            index_chunk(
                chunk=self.chunk,
                embedding_service=Mock(),
            )

    def test_wrong_embedding_dimension_is_rejected(self):
        embedding_service = Mock()

        embedding_service.embed_text.return_value = [
            0.1
        ] * 100

        with self.assertRaises(IndexingError):
            index_chunk(
                chunk=self.chunk,
                embedding_service=embedding_service,
            )

        self.assertFalse(
            ChunkEmbedding.objects.filter(
                document_chunk=self.chunk
            ).exists()
        )


class IndexDocumentVersionTests(TestCase):
    """Tests for indexing complete document versions."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="teacher2@example.com",
            password="testpassword",
            role=User.Roles.TEACHER,
        )

        institution = Institution.objects.create(
            name="Test Institution 2",
            short_name="TEST2",
            email="test2@example.com",
            phone_number="1234567890",
        )

        department = Department.objects.create(
            institution=institution,
            name="Computer Science",
            code="CSE",
        )

        course = Course.objects.create(
            department=department,
            name="Bachelor of Computer Applications",
            code="BCA",
            duration=3,
        )

        semester = Semester.objects.create(
            course=course,
            semester_number=1,
            name="Semester 1",
        )

        subject = Subject.objects.create(
            semester=semester,
            code="DBMS",
            name="Database Management Systems",
        )

        self.document = Document.objects.create(
            title="DBMS Complete Notes",
            description="Complete DBMS notes.",
            subject=subject,
            created_by=self.user,
            status=Document.Status.APPROVED,
            is_active=True,
        )

        self.version = DocumentVersion.objects.create(
            document=self.document,
            version_number=1,
            source_file="documents/test2.pdf",
            original_filename="test2.pdf",
            content_type="application/pdf",
            file_size=100,
            file_checksum="test-checksum-2",
            uploaded_by=self.user,
            review_status=DocumentVersion.ReviewStatus.APPROVED,
            processing_status=DocumentVersion.ProcessingStatus.COMPLETED,
        )

        self.document.published_version = self.version
        self.document.save(update_fields=["published_version"])

        self.chunks = [
            DocumentChunk.objects.create(
                document_version=self.version,
                chunk_index=0,
                content="Introduction to databases.",
            ),
            DocumentChunk.objects.create(
                document_version=self.version,
                chunk_index=1,
                content="Relational database concepts.",
            ),
            DocumentChunk.objects.create(
                document_version=self.version,
                chunk_index=2,
                content="SQL and database queries.",
            ),
        ]

    def test_index_document_version_indexes_all_chunks(self):
        result = index_document_version(
            document_version_id=self.version.pk,
        )

        self.assertEqual(
            result,
            3,
        )

        self.assertEqual(
            ChunkEmbedding.objects.filter(
                document_chunk__document_version=self.version
            ).count(),
            3,
        )

    def test_unpublished_version_is_rejected(self):
        self.document.published_version = None
        self.document.save(update_fields=["published_version"])

        with self.assertRaises(IndexingError):
            index_document_version(
                document_version_id=self.version.pk,
            )

    def test_unapproved_version_is_rejected(self):
        self.version.review_status = (
            DocumentVersion.ReviewStatus.DRAFT
        )
        self.version.save(update_fields=["review_status"])

        with self.assertRaises(IndexingError):
            index_document_version(
                document_version_id=self.version.pk,
            )