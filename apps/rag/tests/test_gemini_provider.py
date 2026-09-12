from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.rag.generation import GenerationError
from apps.rag.generation.providers import (
    GeminiProvider,
    LLMProvider,
)


class GeminiProviderTests(SimpleTestCase):
    """Tests for the Gemini LLM provider."""

    @override_settings(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-gemini-model",
    )
    @patch("apps.rag.generation.providers.gemini.genai.Client")
    def test_provider_implements_llm_provider(
        self,
        mock_client,
    ):
        provider = GeminiProvider()

        self.assertIsInstance(
            provider,
            LLMProvider,
        )

        mock_client.assert_called_once_with(
            api_key="test-gemini-key",
        )

    @override_settings(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-gemini-model",
    )
    @patch("apps.rag.generation.providers.gemini.genai.Client")
    def test_generate_returns_answer(
        self,
        mock_client,
    ):
        mock_instance = mock_client.return_value

        mock_instance.models.generate_content.return_value = (
            SimpleNamespace(
                text="  Test generated answer.  "
            )
        )

        provider = GeminiProvider()

        result = provider.generate(
            "Test RAG prompt."
        )

        self.assertEqual(
            result,
            "Test generated answer.",
        )

        mock_instance.models.generate_content.assert_called_once_with(
            model="test-gemini-model",
            contents="Test RAG prompt.",
        )

    @override_settings(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-gemini-model",
    )
    @patch("apps.rag.generation.providers.gemini.genai.Client")
    def test_generate_rejects_non_string_prompt(
        self,
        mock_client,
    ):
        provider = GeminiProvider()

        with self.assertRaises(GenerationError):
            provider.generate(123)

        mock_client.return_value.models.generate_content.assert_not_called()

    @override_settings(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-gemini-model",
    )
    @patch("apps.rag.generation.providers.gemini.genai.Client")
    def test_generate_rejects_empty_prompt(
        self,
        mock_client,
    ):
        provider = GeminiProvider()

        with self.assertRaises(GenerationError):
            provider.generate("   ")

        mock_client.return_value.models.generate_content.assert_not_called()

    @override_settings(
        GEMINI_API_KEY="",
        GEMINI_MODEL="test-gemini-model",
    )
    def test_missing_api_key_is_rejected(self):
        with self.assertRaises(GenerationError):
            GeminiProvider()

    @override_settings(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="",
    )
    def test_missing_model_is_rejected(self):
        with self.assertRaises(GenerationError):
            GeminiProvider()

    @override_settings(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-gemini-model",
    )
    @patch("apps.rag.generation.providers.gemini.genai.Client")
    def test_api_failure_is_converted_to_generation_error(
        self,
        mock_client,
    ):
        mock_instance = mock_client.return_value

        mock_instance.models.generate_content.side_effect = (
            RuntimeError("Gemini unavailable")
        )

        provider = GeminiProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")

    @override_settings(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-gemini-model",
    )
    @patch("apps.rag.generation.providers.gemini.genai.Client")
    def test_invalid_response_is_rejected(
        self,
        mock_client,
    ):
        mock_instance = mock_client.return_value

        mock_instance.models.generate_content.return_value = (
            SimpleNamespace()
        )

        provider = GeminiProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")

    @override_settings(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-gemini-model",
    )
    @patch("apps.rag.generation.providers.gemini.genai.Client")
    def test_empty_response_is_rejected(
        self,
        mock_client,
    ):
        mock_instance = mock_client.return_value

        mock_instance.models.generate_content.return_value = (
            SimpleNamespace(
                text="   "
            )
        )

        provider = GeminiProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")