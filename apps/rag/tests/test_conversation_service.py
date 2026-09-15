from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.academics.models import (
    Course,
    Department,
    Institution,
    Semester,
    Subject,
)
from apps.rag.conversations import (
    ConversationNotFoundError,
    ConversationService,
    ConversationValidationError,
)
from apps.rag.models import ChatMessage, Conversation

class ConversationServiceTestMixin:
    def create_academic_structure(self):
        institution = Institution.objects.create(
            name="Test Institution",
            short_name="TI",
            email="institution@example.com",
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


class ConversationServiceTests(
    ConversationServiceTestMixin,
    TestCase,
):
    def setUp(self):
        self.user = User.objects.create_user(
            email="service@example.com",
            password="test-password",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="test-password",
        )

        self.subject = self.create_academic_structure()
        self.service = ConversationService()

    def test_create_conversation(self):
        conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
            title="DBMS Questions",
        )

        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.subject, self.subject)
        self.assertEqual(conversation.title, "DBMS Questions")
        self.assertTrue(conversation.is_active)

    def test_list_conversations_returns_only_users_active_conversations(
        self,
    ):
        first = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
            title="First",
        )

        self.service.create_conversation(
            user=self.other_user,
            subject=self.subject,
            title="Other User",
        )

        inactive = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
            title="Inactive",
        )
        inactive.is_active = False
        inactive.save(update_fields=["is_active"])

        conversations = list(
            self.service.list_conversations(user=self.user)
        )

        self.assertEqual(conversations, [first])

    def test_get_conversation_enforces_user_ownership(self):
        conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
            title="Private Conversation",
        )

        with self.assertRaises(ConversationNotFoundError):
            self.service.get_conversation(
                user=self.other_user,
                conversation_id=conversation.id,
            )

    def test_add_user_message(self):
        conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
        )

        message = self.service.add_user_message(
            user=self.user,
            conversation_id=conversation.id,
            content="What is normalization?",
        )

        self.assertEqual(message.conversation, conversation)
        self.assertEqual(message.role, ChatMessage.Role.USER)
        self.assertEqual(message.content, "What is normalization?")
        self.assertEqual(message.sequence, 1)
        self.assertEqual(message.metadata, {})

    def test_add_assistant_message_stores_sources(self):
        conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
        )

        sources = [
            {
                "document_id": 12,
                "document_title": "DBMS Notes",
                "chunk_id": 45,
                "page_number": 7,
            }
        ]

        message = self.service.add_assistant_message(
            user=self.user,
            conversation_id=conversation.id,
            content="Normalization reduces redundancy.",
            sources=sources,
        )

        self.assertEqual(message.role, ChatMessage.Role.ASSISTANT)
        self.assertEqual(message.sequence, 1)
        self.assertEqual(message.metadata["sources"], sources)

    def test_message_sequences_increment(self):
        conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
        )

        first = self.service.add_user_message(
            user=self.user,
            conversation_id=conversation.id,
            content="Question one",
        )

        second = self.service.add_assistant_message(
            user=self.user,
            conversation_id=conversation.id,
            content="Answer one",
        )

        third = self.service.add_user_message(
            user=self.user,
            conversation_id=conversation.id,
            content="Question two",
        )

        self.assertEqual(first.sequence, 1)
        self.assertEqual(second.sequence, 2)
        self.assertEqual(third.sequence, 3)

    def test_invalid_message_content_is_rejected(self):
        conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
        )

        with self.assertRaises(ConversationValidationError):
            self.service.add_user_message(
                user=self.user,
                conversation_id=conversation.id,
                content="   ",
            )

    def test_inactive_conversation_cannot_receive_messages(self):
        conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
        )

        conversation.is_active = False
        conversation.save(update_fields=["is_active"])

        with self.assertRaises(ConversationNotFoundError):
            self.service.add_user_message(
                user=self.user,
                conversation_id=conversation.id,
                content="Should fail",
            )
    def test_add_message_locks_conversation_row(self):
        conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
        )

        with patch.object(
            Conversation.objects,
            "select_for_update",
            wraps=Conversation.objects.select_for_update,
        ) as mock_select_for_update:
            message = self.service.add_user_message(
                user=self.user,
                conversation_id=conversation.id,
                content="Test locking behavior",
            )

        self.assertIsNotNone(message)
        mock_select_for_update.assert_called_once()