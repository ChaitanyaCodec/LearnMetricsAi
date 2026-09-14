from django.test import TestCase

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

from django.test import TestCase, override_settings


from apps.rag.models import ChatMessage




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





class ConversationHistoryTests(
    ConversationServiceTestMixin,
    TestCase,
):
    def setUp(self):
        self.user = User.objects.create_user(
            email="history@example.com",
            password="test-password",
        )

        self.other_user = User.objects.create_user(
            email="other-history@example.com",
            password="test-password",
        )

        self.subject = self.create_academic_structure()
        self.service = ConversationService()

        self.conversation = self.service.create_conversation(
            user=self.user,
            subject=self.subject,
            title="History Test",
        )

    def test_history_is_returned_in_chronological_order(self):
        messages = []

        for index in range(4):
            messages.append(
                self.service.add_user_message(
                    user=self.user,
                    conversation_id=self.conversation.id,
                    content=f"Message {index + 1}",
                )
            )

        history = self.service.get_conversation_history(
            user=self.user,
            conversation_id=self.conversation.id,
        )

        self.assertEqual(
            [message.id for message in history],
            [message.id for message in messages],
        )

    def test_history_limit_returns_latest_messages(self):
        for index in range(6):
            self.service.add_user_message(
                user=self.user,
                conversation_id=self.conversation.id,
                content=f"Message {index + 1}",
            )

        history = self.service.get_conversation_history(
            user=self.user,
            conversation_id=self.conversation.id,
            limit=3,
        )

        self.assertEqual(
            [message.content for message in history],
            [
                "Message 4",
                "Message 5",
                "Message 6",
            ],
        )

    def test_empty_conversation_returns_empty_history(self):
        history = self.service.get_conversation_history(
            user=self.user,
            conversation_id=self.conversation.id,
        )

        self.assertEqual(history, [])

    def test_other_user_cannot_access_conversation_history(self):
        with self.assertRaises(ConversationNotFoundError):
            self.service.get_conversation_history(
                user=self.other_user,
                conversation_id=self.conversation.id,
            )

    def test_invalid_limit_is_rejected(self):
        with self.assertRaises(ConversationValidationError):
            self.service.get_conversation_history(
                user=self.user,
                conversation_id=self.conversation.id,
                limit=0,
            )

    def test_limit_above_maximum_is_rejected(self):
        with self.assertRaises(ConversationValidationError):
            self.service.get_conversation_history(
                user=self.user,
                conversation_id=self.conversation.id,
                limit=51,
            )

    @override_settings(RAG_CONVERSATION_HISTORY_LIMIT=2)
    def test_default_limit_uses_setting(self):
        for index in range(4):
            self.service.add_user_message(
                user=self.user,
                conversation_id=self.conversation.id,
                content=f"Message {index + 1}",
            )

        history = self.service.get_conversation_history(
            user=self.user,
            conversation_id=self.conversation.id,
        )

        self.assertEqual(
            [message.content for message in history],
            [
                "Message 3",
                "Message 4",
            ],
        )