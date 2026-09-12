from types import SimpleNamespace
from unittest.mock import  patch

from django.test import SimpleTestCase, override_settings

from apps.rag.generation import GenerationError
from apps.rag.generation.providers import (
    GroqProvider,
    LLMProvider,
)


class GroqProviderTests(SimpleTestCase):
    """Tests for the Groq LLM provider."""

    @override_settings(
        GROQ_API_KEY="test-groq-key",
        GROQ_MODEL="test-groq-model",
    )
    @patch("apps.rag.generation.providers.groq.Groq")
    def test_provider_implements_llm_provider(
        self,
        mock_groq,
    ):
        provider = GroqProvider()

        self.assertIsInstance(
            provider,
            LLMProvider,
        )

        mock_groq.assert_called_once_with(
            api_key="test-groq-key",
        )

    @override_settings(
        GROQ_API_KEY="test-groq-key",
        GROQ_MODEL="test-groq-model",
    )
    @patch("apps.rag.generation.providers.groq.Groq")
    def test_generate_returns_answer(
        self,
        mock_groq,
    ):
        mock_client = mock_groq.return_value

        mock_client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="  Test generated answer.  "
                        )
                    )
                ]
            )
        )

        provider = GroqProvider()

        result = provider.generate(
            "Test RAG prompt."
        )

        self.assertEqual(
            result,
            "Test generated answer.",
        )

        mock_client.chat.completions.create.assert_called_once_with(
            model="test-groq-model",
            messages=[
                {
                    "role": "user",
                    "content": "Test RAG prompt.",
                }
            ],
        )

    @override_settings(
        GROQ_API_KEY="test-groq-key",
        GROQ_MODEL="test-groq-model",
    )
    @patch("apps.rag.generation.providers.groq.Groq")
    def test_generate_rejects_non_string_prompt(
        self,
        mock_groq,
    ):
        provider = GroqProvider()

        with self.assertRaises(GenerationError):
            provider.generate(123)

        mock_groq.return_value.chat.completions.create.assert_not_called()

    @override_settings(
        GROQ_API_KEY="test-groq-key",
        GROQ_MODEL="test-groq-model",
    )
    @patch("apps.rag.generation.providers.groq.Groq")
    def test_generate_rejects_empty_prompt(
        self,
        mock_groq,
    ):
        provider = GroqProvider()

        with self.assertRaises(GenerationError):
            provider.generate("   ")

        mock_groq.return_value.chat.completions.create.assert_not_called()

    @override_settings(
        GROQ_API_KEY="",
        GROQ_MODEL="test-groq-model",
    )
    def test_missing_api_key_is_rejected(self):
        with self.assertRaises(GenerationError):
            GroqProvider()

    @override_settings(
        GROQ_API_KEY="test-groq-key",
        GROQ_MODEL="",
    )
    def test_missing_model_is_rejected(self):
        with self.assertRaises(GenerationError):
            GroqProvider()

    @override_settings(
        GROQ_API_KEY="test-groq-key",
        GROQ_MODEL="test-groq-model",
    )
    @patch("apps.rag.generation.providers.groq.Groq")
    def test_api_failure_is_converted_to_generation_error(
        self,
        mock_groq,
    ):
        mock_client = mock_groq.return_value

        mock_client.chat.completions.create.side_effect = (
            RuntimeError("Groq unavailable")
        )

        provider = GroqProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")

    @override_settings(
        GROQ_API_KEY="test-groq-key",
        GROQ_MODEL="test-groq-model",
    )
    @patch("apps.rag.generation.providers.groq.Groq")
    def test_invalid_response_is_rejected(
        self,
        mock_groq,
    ):
        mock_client = mock_groq.return_value

        mock_client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[]
            )
        )

        provider = GroqProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")

    @override_settings(
        GROQ_API_KEY="test-groq-key",
        GROQ_MODEL="test-groq-model",
    )
    @patch("apps.rag.generation.providers.groq.Groq")
    def test_empty_response_is_rejected(
        self,
        mock_groq,
    ):
        mock_client = mock_groq.return_value

        mock_client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="   "
                        )
                    )
                ]
            )
        )

        provider = GroqProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")