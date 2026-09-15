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
from apps.rag.models import ChunkEmbedding
from apps.rag.retrieval import RetrievalError, RetrievalService


class RetrievalServiceTests(TestCase):
    """Tests for vector-based document chunk retrieval."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="retrieval@example.com",
            password="testpassword",
            role=User.Roles.TEACHER,
        )

        institution = Institution.objects.create(
            name="Retrieval Test Institution",
            short_name="RTI",
            email="retrieval@example.com",
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

        self.other_subject = Subject.objects.create(
            semester=semester,
            code="OS",
            name="Operating Systems",
        )

        self.document = Document.objects.create(
            title="DBMS Notes",
            description="Database management notes.",
            subject=self.subject,
            created_by=self.user,
            status=Document.Status.APPROVED,
            is_active=True,
        )

        self.version = DocumentVersion.objects.create(
            document=self.document,
            version_number=1,
            source_file="documents/retrieval.pdf",
            original_filename="retrieval.pdf",
            content_type="application/pdf",
            file_size=100,
            file_checksum="retrieval-checksum",
            uploaded_by=self.user,
            review_status=DocumentVersion.ReviewStatus.APPROVED,
            processing_status=(
                DocumentVersion.ProcessingStatus.COMPLETED
            ),
        )

        self.document.published_version = self.version
        self.document.save(
            update_fields=["published_version"]
        )

        self.chunk_1 = DocumentChunk.objects.create(
            document_version=self.version,
            chunk_index=0,
            content="Database management systems store data.",
        )

        self.chunk_2 = DocumentChunk.objects.create(
            document_version=self.version,
            chunk_index=1,
            content="SQL is used to query relational databases.",
        )

        self.chunk_3 = DocumentChunk.objects.create(
            document_version=self.version,
            chunk_index=2,
            content="Database normalization reduces redundancy.",
        )

        self.embedding_1 = self._create_embedding(
            self.chunk_1,
            1.0,
        )

        self.embedding_2 = self._create_embedding(
            self.chunk_2,
            0.8,
        )

        self.embedding_3 = self._create_embedding(
            self.chunk_3,
            0.6,
        )

        self.service = RetrievalService()

    @staticmethod
    def _create_embedding(chunk, value):
        vector = [0.0] * 384
        vector[0] = value

        return ChunkEmbedding.objects.create(
            document_chunk=chunk,
            embedding=vector,
            model_name=(
                "sentence-transformers/"
                "all-MiniLM-L6-v2"
            ),
            model_version="",
            dimensions=384,
        )

    def test_retrieve_returns_indexed_chunks(self):
        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=3,
        )

        self.assertEqual(len(results), 3)

        self.assertIn(
            self.chunk_1,
            results,
        )

    def test_top_k_limits_results(self):
        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=2,
        )

        self.assertEqual(len(results), 2)

    def test_results_are_ordered_by_similarity(self):
        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=3,
        )

        distances = [
            result.distance
            for result in results
        ]

        self.assertEqual(
            distances,
            sorted(distances),
        )

    def test_chunks_without_embeddings_are_excluded(self):
        chunk = DocumentChunk.objects.create(
            document_version=self.version,
            chunk_index=3,
            content="This chunk has no embedding.",
        )

        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=10,
        )

        self.assertNotIn(chunk, results)

    def test_wrong_embedding_dimension_is_rejected(self):
        with self.assertRaises(RetrievalError):
            self.service.retrieve(
                query_embedding=[0.0] * 100,
            )

    def test_empty_embedding_is_rejected(self):
        with self.assertRaises(RetrievalError):
            self.service.retrieve(
                query_embedding=[],
            )

    def test_invalid_embedding_type_is_rejected(self):
        with self.assertRaises(RetrievalError):
            self.service.retrieve(
                query_embedding="invalid",
            )

    def test_invalid_top_k_is_rejected(self):
        query_embedding = [0.0] * 384

        with self.assertRaises(RetrievalError):
            self.service.retrieve(
                query_embedding=query_embedding,
                top_k=0,
            )

    def test_top_k_above_maximum_is_rejected(self):
        query_embedding = [0.0] * 384

        with self.assertRaises(RetrievalError):
            self.service.retrieve(
                query_embedding=query_embedding,
                top_k=21,
            )

    def test_unpublished_version_is_excluded(self):
        self.document.published_version = None
        self.document.save(
            update_fields=["published_version"]
        )

        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=10,
        )

        self.assertEqual(results, [])

    def test_unapproved_document_is_excluded(self):
        self.document.status = Document.Status.DRAFT
        self.document.save(
            update_fields=["status"]
        )

        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=10,
        )

        self.assertEqual(results, [])

    def test_inactive_document_is_excluded(self):
        self.document.is_active = False
        self.document.save(
            update_fields=["is_active"]
        )

        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=10,
        )

        self.assertEqual(results, [])

    def test_subject_filter_is_applied(self):
        other_document = Document.objects.create(
            title="OS Notes",
            description="Operating systems notes.",
            subject=self.other_subject,
            created_by=self.user,
            status=Document.Status.APPROVED,
            is_active=True,
        )

        other_version = DocumentVersion.objects.create(
            document=other_document,
            version_number=1,
            source_file="documents/os.pdf",
            original_filename="os.pdf",
            content_type="application/pdf",
            file_size=100,
            file_checksum="os-checksum",
            uploaded_by=self.user,
            review_status=(
                DocumentVersion.ReviewStatus.APPROVED
            ),
            processing_status=(
                DocumentVersion.ProcessingStatus.COMPLETED
            ),
        )

        other_document.published_version = other_version
        other_document.save(
            update_fields=["published_version"]
        )

        other_chunk = DocumentChunk.objects.create(
            document_version=other_version,
            chunk_index=0,
            content="Operating system process management.",
        )

        self._create_embedding(
            other_chunk,
            1.0,
        )

        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=10,
            subject=self.subject,
        )

        self.assertTrue(results)

        for result in results:
            self.assertEqual(
                result.document_version.document.subject,
                self.subject,
            )

    def test_unapproved_document_version_is_excluded(self):
        self.version.review_status = (
            DocumentVersion.ReviewStatus.REJECTED
        )
        self.version.save(update_fields=["review_status"])

        query_embedding = [1.0] + [0.0] * 383

        results = self.service.retrieve(
            query_embedding=query_embedding,
        )

        self.assertEqual(results, [])

    def test_unapproved_document_version_is_excluded(self):
        self.version.review_status = (
            DocumentVersion.ReviewStatus.REJECTED
        )
        self.version.save(update_fields=["review_status"])

        query_embedding = [1.0] + [0.0] * 383

        results = self.service.retrieve(
            query_embedding=query_embedding,
        )

        self.assertEqual(results, [])


    def test_incomplete_processing_version_is_excluded(self):
        self.version.processing_status = (
            DocumentVersion.ProcessingStatus.PROCESSING
        )
        self.version.save(update_fields=["processing_status"])

        query_embedding = [1.0] + [0.0] * 383

        results = self.service.retrieve(
            query_embedding=query_embedding,
        )

        self.assertEqual(results, [])


    def test_old_document_version_is_excluded_when_newer_version_is_published(
        self,
    ):
        old_version = self.version

        old_chunk = DocumentChunk.objects.filter(
            document_version=old_version,
        ).first()

        self.assertIsNotNone(old_chunk)

        newer_version = DocumentVersion.objects.create(
            document=self.document,
            version_number=2,
            source_file="documents/test-v2.pdf",
            original_filename="test-v2.pdf",
            content_type="application/pdf",
            file_size=100,
            file_checksum="b" * 64,
            uploaded_by=self.user,
            review_status=DocumentVersion.ReviewStatus.APPROVED,
            processing_status=DocumentVersion.ProcessingStatus.COMPLETED,
        )

        new_chunk = DocumentChunk.objects.create(
            document_version=newer_version,
            chunk_index=0,
            content="Content from the new published document version.",
        )

        self._create_embedding(
            new_chunk,
            1.0,
        )
        self.document.published_version = newer_version
        self.document.save(
            update_fields=["published_version"],
        )

        query_embedding = [1.0] + [0.0] * 383

        results = self.service.retrieve(
            query_embedding=query_embedding,
        )

        result_ids = [chunk.id for chunk in results]

        self.assertIn(new_chunk.id, result_ids)
        self.assertNotIn(old_chunk.id, result_ids)


    def test_distance_threshold_excludes_irrelevant_chunks(self):
        irrelevant_chunk = DocumentChunk.objects.create(
            document_version=self.version,
            chunk_index=3,
            content="This chunk is intentionally unrelated.",
        )

        irrelevant_vector = [0.0] * 384
        irrelevant_vector[1] = 1.0

        ChunkEmbedding.objects.create(
            document_chunk=irrelevant_chunk,
            embedding=irrelevant_vector,
            model_name=(
                "sentence-transformers/"
                "all-MiniLM-L6-v2"
            ),
            model_version="",
            dimensions=384,
        )

        query_embedding = [0.0] * 384
        query_embedding[0] = 1.0

        results = self.service.retrieve(
            query_embedding=query_embedding,
            top_k=10,
        )

        self.assertNotIn(
            irrelevant_chunk,
            results,
        )