import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from apps.accounts.models import User
from apps.rag.services import RagAnswer, RagServiceError
from apps.rag.views import RagAskAPIView


class RagAskAPIViewTests(SimpleTestCase):
    """
    Tests for the RAG question-answer API endpoint.
    """
    @staticmethod
    def _serialize_sources(chunks):
        return _serialize_sources(chunks)
    def setUp(self):
        self.factory = RequestFactory()
        self.url = "/rag/ask/"

    def make_request(self, payload, user):
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        request.user = user

        return RagAskAPIView.as_view()(request)

    def test_question_must_be_provided(self):
        user = self._make_user()

        response = self.make_request(
            {
                "subject_id": 1,
            },
            user,
        )

        self.assertEqual(response.status_code, 400)

    def test_question_must_be_string(self):
        user = self._make_user()

        response = self.make_request(
            {
                "question": 123,
                "subject_id": 1,
            },
            user,
        )

        self.assertEqual(response.status_code, 400)

    def test_empty_question_is_rejected(self):
        user = self._make_user()

        response = self.make_request(
            {
                "question": "   ",
                "subject_id": 1,
            },
            user,
        )

        self.assertEqual(response.status_code, 400)

    def test_subject_id_is_required(self):
        user = self._make_user()

        response = self.make_request(
            {
                "question": "What is normalization?",
            },
            user,
        )

        self.assertEqual(response.status_code, 400)

    def test_subject_id_must_be_integer(self):
        user = self._make_user()

        response = self.make_request(
            {
                "question": "What is normalization?",
                "subject_id": "1",
            },
            user,
        )

        self.assertEqual(response.status_code, 400)

    def test_top_k_must_be_integer(self):
        user = self._make_user()

        response = self.make_request(
            {
                "question": "What is normalization?",
                "subject_id": 1,
                "top_k": "5",
            },
            user,
        )

        self.assertEqual(response.status_code, 400)

    @patch("apps.rag.views.Subject.objects.get")
    @patch(
        "apps.rag.views.is_documents_admin",
        return_value=False,
    )
    @patch(
        "apps.rag.views.student_can_access_subject",
        return_value=False,
    )
    @patch(
        "apps.rag.views.teacher_can_upload_for_subject",
        return_value=False,
    )
    def test_inaccessible_subject_is_rejected(
        self,
        mock_teacher_access,
        mock_student_access,
        mock_admin,
        mock_subject_get,
    ):
        user = self._make_user()

        subject = object()
        mock_subject_get.return_value = subject

        response = self.make_request(
            {
                "question": "What is normalization?",
                "subject_id": 1,
            },
            user,
        )

        self.assertEqual(response.status_code, 403)

        mock_subject_get.assert_called_once_with(
            pk=1
        )

    @patch("apps.rag.views.Subject.objects.get")
    @patch(
        "apps.rag.views.is_documents_admin",
        return_value=True,
    )
    @patch("apps.rag.views.RagService")
    def test_admin_can_ask_question(
        self,
        mock_rag_service,
        mock_admin,
        mock_subject_get,
    ):
        user = self._make_user()

        subject = object()
        mock_subject_get.return_value = subject

        result = RagAnswer(
            answer=(
                "Normalization is the process of "
                "organizing data."
            ),
            chunks=(),
        )

        mock_service = mock_rag_service.return_value
        mock_service.answer_question_with_sources.return_value = (
            result
        )

        response = self.make_request(
            {
                "question": "What is normalization?",
                "subject_id": 1,
                "top_k": 5,
            },
            user,
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(
            data["answer"],
            (
                "Normalization is the process of "
                "organizing data."
            ),
        )

        self.assertEqual(
            data["sources"],
            [],
        )

        mock_service.answer_question_with_sources.assert_called_once_with(
            user=user,
            question="What is normalization?",
            subject=subject,
            top_k=5,
        )

    @patch("apps.rag.views.Subject.objects.get")
    @patch(
        "apps.rag.views.is_documents_admin",
        return_value=True,
    )
    @patch("apps.rag.views.RagService")
    def test_top_k_is_optional(
        self,
        mock_rag_service,
        mock_admin,
        mock_subject_get,
    ):
        user = self._make_user()

        subject = object()
        mock_subject_get.return_value = subject

        result = RagAnswer(
            answer="Answer",
            chunks=(),
        )

        mock_service = mock_rag_service.return_value
        mock_service.answer_question_with_sources.return_value = (
            result
        )

        response = self.make_request(
            {
                "question": "What is normalization?",
                "subject_id": 1,
            },
            user,
        )

        self.assertEqual(response.status_code, 200)

        mock_service.answer_question_with_sources.assert_called_once_with(
            user=user,
            question="What is normalization?",
            subject=subject,
            top_k=None,
        )

    @patch("apps.rag.views.Subject.objects.get")
    @patch(
        "apps.rag.views.is_documents_admin",
        return_value=True,
    )
    def test_missing_subject_returns_404(
        self,
        mock_admin,
        mock_subject_get,
    ):
        from apps.academics.models import Subject

        user = self._make_user()

        mock_subject_get.side_effect = Subject.DoesNotExist

        response = self.make_request(
            {
                "question": "What is normalization?",
                "subject_id": 999,
            },
            user,
        )

        self.assertEqual(response.status_code, 404)

    @patch("apps.rag.views.Subject.objects.get")
    @patch(
        "apps.rag.views.is_documents_admin",
        return_value=True,
    )
    @patch("apps.rag.views.RagService")
    def test_rag_service_failure_returns_500(
        self,
        mock_rag_service,
        mock_admin,
        mock_subject_get,
    ):
        user = self._make_user()

        subject = object()
        mock_subject_get.return_value = subject

        mock_service = mock_rag_service.return_value
        mock_service.answer_question_with_sources.side_effect = (
            RagServiceError("Generation failed.")
        )

        response = self.make_request(
            {
                "question": "What is normalization?",
                "subject_id": 1,
            },
            user,
        )

        self.assertEqual(response.status_code, 500)

    @patch("apps.rag.views.Subject.objects.get")
    @patch(
        "apps.rag.views.is_documents_admin",
        return_value=True,
    )
    @patch("apps.rag.views.RagService")
    def test_sources_are_returned(
        self,
        mock_rag_service,
        mock_admin,
        mock_subject_get,
    ):
        user = self._make_user()

        document = SimpleNamespace(
            id=12,
            title="DBMS Notes",
        )

        document_version = SimpleNamespace(
            document=document,
        )

        chunk = SimpleNamespace(
            id=45,
            page_number=7,
            document_version=document_version,
        )

        subject = object()
        mock_subject_get.return_value = subject

        result = RagAnswer(
            answer="Normalization organizes relational data.",
            chunks=(chunk,),
        )

        mock_service = mock_rag_service.return_value
        mock_service.answer_question_with_sources.return_value = (
            result
        )

        response = self.make_request(
            {
                "question": "What is normalization?",
                "subject_id": 1,
                "top_k": 5,
            },
            user,
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(
            data["answer"],
            "Normalization organizes relational data.",
        )

        self.assertEqual(
            data["sources"],
            [
                {
                    "document_id": 12,
                    "document_title": "DBMS Notes",
                    "chunk_id": 45,
                    "page_number": 7,
                }
            ],
        )

    def test_source_without_document_is_skipped(self):
        chunk = SimpleNamespace(
            id=45,
            page_number=7,
            document_version=None,
        )

        sources = RagAskAPIView._serialize_sources(
            (chunk,)
        )

        self.assertEqual(sources, [])

    def _make_user(self):
        class TestUser:
            is_authenticated = True
            is_active = True
            role = User.Roles.STUDENT

        return TestUser()