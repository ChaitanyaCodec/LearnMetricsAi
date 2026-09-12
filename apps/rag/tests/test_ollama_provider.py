from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from apps.rag.generation import GenerationError
from apps.rag.generation.providers import (
    LLMProvider,
    OllamaProvider,
)


class OllamaProviderTests(SimpleTestCase):
    """Tests for the Ollama LLM provider."""

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="qwen2.5:3b",
    )
    def test_provider_implements_llm_provider(self):
        provider = OllamaProvider()

        self.assertIsInstance(
            provider,
            LLMProvider,
        )

        self.assertEqual(
            provider.base_url,
            "http://localhost:11434",
        )

        self.assertEqual(
            provider.model,
            "qwen2.5:3b",
        )

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="qwen2.5:3b",
    )
    @patch("apps.rag.generation.providers.ollama.requests.post")
    def test_generate_returns_answer(
        self,
        mock_post,
    ):
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "  Test generated answer.  "
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()

        result = provider.generate(
            "Test RAG prompt."
        )

        self.assertEqual(
            result,
            "Test generated answer.",
        )

        mock_post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:3b",
                "prompt": "Test RAG prompt.",
                "stream": False,
            },
            timeout=120,
        )

        mock_response.raise_for_status.assert_called_once()

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="qwen2.5:3b",
    )
    @patch("apps.rag.generation.providers.ollama.requests.post")
    def test_generate_rejects_non_string_prompt(
        self,
        mock_post,
    ):
        provider = OllamaProvider()

        with self.assertRaises(GenerationError):
            provider.generate(123)

        mock_post.assert_not_called()

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="qwen2.5:3b",
    )
    @patch("apps.rag.generation.providers.ollama.requests.post")
    def test_generate_rejects_empty_prompt(
        self,
        mock_post,
    ):
        provider = OllamaProvider()

        with self.assertRaises(GenerationError):
            provider.generate("   ")

        mock_post.assert_not_called()

    @override_settings(
        OLLAMA_BASE_URL="",
        OLLAMA_MODEL="qwen2.5:3b",
    )
    def test_missing_base_url_is_rejected(self):
        with self.assertRaises(GenerationError):
            OllamaProvider()

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="",
    )
    def test_missing_model_is_rejected(self):
        with self.assertRaises(GenerationError):
            OllamaProvider()

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="qwen2.5:3b",
    )
    @patch("apps.rag.generation.providers.ollama.requests.post")
    def test_api_failure_is_converted_to_generation_error(
        self,
        mock_post,
    ):
        import requests

        mock_post.side_effect = requests.RequestException(
            "Ollama unavailable"
        )

        provider = OllamaProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="qwen2.5:3b",
    )
    @patch("apps.rag.generation.providers.ollama.requests.post")
    def test_invalid_response_is_rejected(
        self,
        mock_post,
    ):
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        provider = OllamaProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="qwen2.5:3b",
    )
    @patch("apps.rag.generation.providers.ollama.requests.post")
    def test_empty_response_is_rejected(
        self,
        mock_post,
    ):
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "   "
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()

        with self.assertRaises(GenerationError):
            provider.generate("Test prompt.")