import json
from unittest.mock import Mock, patch

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
from apps.rag.models import ChatMessage, Conversation
from apps.rag.services import RagAnswer,RagServiceError


class ConversationAPITestMixin:
    def create_academic_structure(self):
        institution = Institution.objects.create(
            name="API Institution",
            short_name="API",
            email="api@example.com",
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

        return Subject.objects.create(
            semester=semester,
            code="DBMS101",
            name="Database Management Systems",
        )


class ConversationAPIAuthenticationTests(
    ConversationAPITestMixin,
    TestCase,
):
    def setUp(self):
        self.user = User.objects.create_user(
            email="api-user@example.com",
            password="test-password",
            role=User.Roles.ADMIN,
        )

        self.subject = self.create_academic_structure()

    def test_conversation_list_requires_login(self):
        response = self.client.get(
            reverse("rag:conversation-list-create")
        )

        self.assertEqual(response.status_code, 302)

    def test_conversation_create_requires_login(self):
        response = self.client.post(
            reverse("rag:conversation-list-create"),
            data=json.dumps(
                {
                    "subject_id": self.subject.id,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 302)


class ConversationAPIWorkflowTests(
    ConversationAPITestMixin,
    TestCase,
):
    def setUp(self):
        self.user = User.objects.create_user(
            email="workflow@example.com",
            password="test-password",
            role=User.Roles.ADMIN,
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="test-password",
        )

        self.subject = self.create_academic_structure()

        self.client.force_login(self.user)

    def test_create_conversation(self):
        response = self.client.post(
            reverse("rag:conversation-list-create"),
            data=json.dumps(
                {
                    "subject_id": self.subject.id,
                    "title": "DBMS Discussion",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        payload = response.json()

        self.assertIn("conversation", payload)
        self.assertEqual(
            payload["conversation"]["title"],
            "DBMS Discussion",
        )
        self.assertEqual(
            payload["conversation"]["subject_id"],
            self.subject.id,
        )

        self.assertEqual(
            Conversation.objects.filter(
                user=self.user
            ).count(),
            1,
        )

    def test_list_conversations_returns_only_current_users_conversations(
        self,
    ):
        Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="My Conversation",
        )

        Conversation.objects.create(
            user=self.other_user,
            subject=self.subject,
            title="Other Conversation",
        )

        response = self.client.get(
            reverse("rag:conversation-list-create")
        )

        self.assertEqual(response.status_code, 200)

        conversations = response.json()["conversations"]

        self.assertEqual(len(conversations), 1)
        self.assertEqual(
            conversations[0]["title"],
            "My Conversation",
        )

    def test_get_conversation_returns_messages(self):
        conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="Existing Conversation",
        )

        ChatMessage.objects.create(
            conversation=conversation,
            role=ChatMessage.Role.USER,
            content="What is normalization?",
            sequence=1,
        )

        response = self.client.get(
            reverse(
                "rag:conversation-detail",
                kwargs={
                    "conversation_id": conversation.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(
            len(payload["conversation"]["messages"]),
            1,
        )

        self.assertEqual(
            payload["conversation"]["messages"][0]["content"],
            "What is normalization?",
        )

    def test_other_user_cannot_get_conversation(self):
        conversation = Conversation.objects.create(
            user=self.other_user,
            subject=self.subject,
            title="Private Conversation",
        )

        response = self.client.get(
            reverse(
                "rag:conversation-detail",
                kwargs={
                    "conversation_id": conversation.id,
                },
            )
        )

        self.assertEqual(response.status_code, 404)

    @patch("apps.rag.views.RagService")
    def test_send_message_persists_user_and_assistant_messages(
        self,
        rag_service_class,
    ):
        conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="DBMS Chat",
        )

        rag_service = rag_service_class.return_value

        rag_service.answer_question_with_sources.return_value = (
            RagAnswer(
                answer="Normalization reduces redundancy.",
                chunks=(),
            )
        )

        response = self.client.post(
            reverse(
                "rag:conversation-message",
                kwargs={
                    "conversation_id": conversation.id,
                },
            ),
            data=json.dumps(
                {
                    "question": "What is normalization?",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            ChatMessage.objects.filter(
                conversation=conversation
            ).count(),
            2,
        )

        messages = list(
            ChatMessage.objects.filter(
                conversation=conversation
            ).order_by("sequence")
        )

        self.assertEqual(
            messages[0].role,
            ChatMessage.Role.USER,
        )

        self.assertEqual(
            messages[0].content,
            "What is normalization?",
        )

        self.assertEqual(
            messages[1].role,
            ChatMessage.Role.ASSISTANT,
        )

        self.assertEqual(
            messages[1].content,
            "Normalization reduces redundancy.",
        )

        self.assertEqual(messages[0].sequence, 1)
        self.assertEqual(messages[1].sequence, 2)

    @patch("apps.rag.views.RagService")
    def test_assistant_sources_are_persisted_in_metadata(
        self,
        rag_service_class,
    ):
        conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="Citation Chat",
        )

        rag_service = rag_service_class.return_value

        rag_service.answer_question_with_sources.return_value = (
            RagAnswer(
                answer="Normalization reduces redundancy.",
                chunks=(),
            )
        )

        response = self.client.post(
            reverse(
                "rag:conversation-message",
                kwargs={
                    "conversation_id": conversation.id,
                },
            ),
            data=json.dumps(
                {
                    "question": "What is normalization?",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        assistant_message = ChatMessage.objects.get(
            conversation=conversation,
            role=ChatMessage.Role.ASSISTANT,
        )

        self.assertEqual(
            assistant_message.metadata["sources"],
            [],
        )

    @patch("apps.rag.views.RagService")
    def test_user_message_remains_when_rag_generation_fails(
        self,
        rag_service_class,
    ):
        conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="Failed RAG Chat",
        )

        rag_service = rag_service_class.return_value
        rag_service.answer_question_with_sources.side_effect = (
            RagServiceError("Generation failed")
        )

        response = self.client.post(
            reverse(
                "rag:conversation-message",
                kwargs={
                    "conversation_id": conversation.id,
                },
            ),
            data=json.dumps(
                {
                    "question": "What is normalization?",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 502)

        messages = ChatMessage.objects.filter(
            conversation=conversation
        )

        self.assertEqual(messages.count(), 1)

        message = messages.first()

        self.assertEqual(
            message.role,
            ChatMessage.Role.USER,
        )

        self.assertEqual(
            message.content,
            "What is normalization?",
        )

    def test_empty_question_is_rejected(self):
        conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="Validation Chat",
        )

        response = self.client.post(
            reverse(
                "rag:conversation-message",
                kwargs={
                    "conversation_id": conversation.id,
                },
            ),
            data=json.dumps(
                {
                    "question": "   ",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            ChatMessage.objects.filter(
                conversation=conversation
            ).count(),
            0,
        )

    def test_invalid_conversation_id_returns_404(self):
        response = self.client.get(
            reverse(
                "rag:conversation-detail",
                kwargs={
                    "conversation_id":
                        "00000000-0000-0000-0000-000000000000",
                },
            )
        )

        self.assertEqual(response.status_code, 404)