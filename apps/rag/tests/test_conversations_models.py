from django.test import TestCase

from apps.accounts.models import User
from apps.academics.models import (
    Course,
    Department,
    Institution,
    Semester,
    Subject,
)
from apps.rag.models import ChatMessage, Conversation


class ConversationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="rag-model@example.com",
            password="test-password",
        )

        self.institution = Institution.objects.create(
            name="Test Institution",
            short_name="TI",
            email="info@ti.edu",
            phone_number="1234567890",
        )

        self.department = Department.objects.create(
            institution=self.institution,
            name="Computer Science",
            code="CS",
        )

        self.course = Course.objects.create(
            department=self.department,
            name="B.Sc. Computer Science",
            code="BSC-CS",  # Added required code field
            duration=3,     # Added required duration field
        )

        self.semester = Semester.objects.create(
            course=self.course,
            name="Semester 1",
            semester_number=1, # Added required semester_number field based on models.py
        )

        self.subject = Subject.objects.create(
            semester=self.semester,
            name="Database Management Systems",
            code="DBMS101",
        )

    def test_conversation_can_be_created(self):
        conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="DBMS Questions",
        )

        self.assertIsNotNone(conversation.id)
        self.assertEqual(
            conversation.user,
            self.user,
        )
        self.assertEqual(
            conversation.subject,
            self.subject,
        )
        self.assertEqual(
            conversation.title,
            "DBMS Questions",
        )
        self.assertTrue(conversation.is_active)

    def test_conversation_has_uuid_primary_key(self):
        conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
        )

        self.assertEqual(
            conversation.id.version,
            4,
        )

    def test_conversation_without_title_has_fallback_string(self):
        conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
        )

        self.assertIn(
            str(conversation.id),
            str(conversation),
        )

    def test_conversation_ordering_uses_updated_at(self):
        first = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="First",
        )

        second = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="Second",
        )

        conversations = list(
            Conversation.objects.all()
        )

        self.assertEqual(
            conversations[0],
            second,
        )

        self.assertEqual(
            conversations[1],
            first,
        )


class ChatMessageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="chat-model@example.com",
            password="test-password",
        )

        self.institution = Institution.objects.create(
            name="Test Institution",
            short_name="TI",
            email="info@ti.edu",
            phone_number="1234567890",
        )

        self.department = Department.objects.create(
            institution=self.institution,
            name="Computer Science",
            code="CS",
        )

        self.course = Course.objects.create(
            department=self.department,
            name="B.Sc. Computer Science",
            code="BSC-CS",  # Added required code field
            duration=3,     # Added required duration field
        )

        self.semester = Semester.objects.create(
            course=self.course,
            name="Semester 1",
            semester_number=1, # Added required semester_number field based on models.py
        )

        self.subject = Subject.objects.create(
            semester=self.semester,
            name="Database Management Systems",
            code="DBMS101",
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="DBMS Questions",
        )

    def test_user_message_can_be_created(self):
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            role=ChatMessage.Role.USER,
            content="What is normalization?",
            sequence=1,
        )

        self.assertIsNotNone(message.id)
        self.assertEqual(
            message.role,
            ChatMessage.Role.USER,
        )
        self.assertEqual(
            message.content,
            "What is normalization?",
        )
        self.assertEqual(
            message.sequence,
            1,
        )
        self.assertEqual(
            message.metadata,
            {},
        )

    def test_assistant_message_can_store_sources(self):
        metadata = {
            "sources": [
                {
                    "document_id": 12,
                    "document_title": "DBMS Notes",
                    "chunk_id": 45,
                    "page_number": 7,
                }
            ]
        }

        message = ChatMessage.objects.create(
            conversation=self.conversation,
            role=ChatMessage.Role.ASSISTANT,
            content="Normalization organizes relational data.",
            sequence=2,
            metadata=metadata,
        )

        self.assertEqual(
            message.role,
            ChatMessage.Role.ASSISTANT,
        )

        self.assertEqual(
            message.metadata,
            metadata,
        )

    def test_message_sequence_must_be_unique_per_conversation(
        self,
    ):
        ChatMessage.objects.create(
            conversation=self.conversation,
            role=ChatMessage.Role.USER,
            content="First question",
            sequence=1,
        )

        with self.assertRaises(Exception):
            ChatMessage.objects.create(
                conversation=self.conversation,
                role=ChatMessage.Role.ASSISTANT,
                content="First answer",
                sequence=1,
            )

    def test_same_sequence_is_allowed_in_different_conversations(
        self,
    ):
        second_conversation = Conversation.objects.create(
            user=self.user,
            subject=self.subject,
            title="Second Conversation",
        )

        first_message = ChatMessage.objects.create(
            conversation=self.conversation,
            role=ChatMessage.Role.USER,
            content="Question one",
            sequence=1,
        )

        second_message = ChatMessage.objects.create(
            conversation=second_conversation,
            role=ChatMessage.Role.USER,
            content="Question two",
            sequence=1,
        )

        self.assertEqual(
            first_message.sequence,
            second_message.sequence,
        )

    def test_message_string_representation(self):
        message = ChatMessage.objects.create(
            conversation=self.conversation,
            role=ChatMessage.Role.USER,
            content="Question",
            sequence=1,
        )

        self.assertIn(
            "USER",
            str(message),
        )

        self.assertIn(
            "1",
            str(message),
        )