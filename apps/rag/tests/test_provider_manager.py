from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.rag.generation import GenerationError
from apps.rag.generation.providers import (
    LLMProvider,
    LLMProviderManager,
)


class TestProvider(LLMProvider):
    """Simple provider used for manager tests."""

    def __init__(self, *, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.calls = []

    def generate(self, prompt):
        self.calls.append(prompt)

        if self.error is not None:
            raise self.error

        return self.answer


class LLMProviderManagerTests(SimpleTestCase):
    """Tests for LLM provider priority and fallback."""

    def test_primary_provider_success(self):
        primary = TestProvider(
            answer="Primary answer"
        )
        secondary = TestProvider(
            answer="Secondary answer"
        )

        manager = LLMProviderManager(
            providers=[
                primary,
                secondary,
            ]
        )

        result = manager.generate(
            "Test prompt."
        )

        self.assertEqual(
            result,
            "Primary answer",
        )

        self.assertEqual(
            primary.calls,
            ["Test prompt."],
        )

        self.assertEqual(
            secondary.calls,
            [],
        )

    def test_falls_back_to_secondary_provider(self):
        primary = TestProvider(
            error=GenerationError(
                "Primary failed."
            )
        )
        secondary = TestProvider(
            answer="Secondary answer"
        )

        manager = LLMProviderManager(
            providers=[
                primary,
                secondary,
            ]
        )

        result = manager.generate(
            "Test prompt."
        )

        self.assertEqual(
            result,
            "Secondary answer",
        )

        self.assertEqual(
            primary.calls,
            ["Test prompt."],
        )

        self.assertEqual(
            secondary.calls,
            ["Test prompt."],
        )

    def test_falls_back_through_all_providers(self):
        primary = TestProvider(
            error=GenerationError(
                "Groq failed."
            )
        )
        secondary = TestProvider(
            error=GenerationError(
                "Gemini failed."
            )
        )
        fallback = TestProvider(
            answer="Ollama answer"
        )

        manager = LLMProviderManager(
            providers=[
                primary,
                secondary,
                fallback,
            ]
        )

        result = manager.generate(
            "Test prompt."
        )

        self.assertEqual(
            result,
            "Ollama answer",
        )

        self.assertEqual(
            primary.calls,
            ["Test prompt."],
        )

        self.assertEqual(
            secondary.calls,
            ["Test prompt."],
        )

        self.assertEqual(
            fallback.calls,
            ["Test prompt."],
        )

    def test_all_providers_failing_raises_generation_error(self):
        primary = TestProvider(
            error=GenerationError(
                "Groq failed."
            )
        )
        secondary = TestProvider(
            error=GenerationError(
                "Gemini failed."
            )
        )
        fallback = TestProvider(
            error=GenerationError(
                "Ollama failed."
            )
        )

        manager = LLMProviderManager(
            providers=[
                primary,
                secondary,
                fallback,
            ]
        )

        with self.assertRaises(GenerationError) as context:
            manager.generate(
                "Test prompt."
            )

        self.assertEqual(
            str(context.exception),
            "All configured LLM providers failed.",
        )

    def test_provider_order_is_preserved(self):
        first = TestProvider(
            error=GenerationError("First failed.")
        )
        second = TestProvider(
            error=GenerationError("Second failed.")
        )
        third = TestProvider(
            answer="Third answer"
        )

        manager = LLMProviderManager(
            providers=[
                first,
                second,
                third,
            ]
        )

        manager.generate(
            "Test prompt."
        )

        self.assertEqual(
            first.calls,
            ["Test prompt."],
        )
        self.assertEqual(
            second.calls,
            ["Test prompt."],
        )
        self.assertEqual(
            third.calls,
            ["Test prompt."],
        )

    def test_manager_rejects_empty_provider_list(self):
        with self.assertRaises(GenerationError):
            LLMProviderManager(
                providers=[]
            )

    def test_manager_rejects_none_providers(self):
        with self.assertRaises(GenerationError):
            LLMProviderManager(
                providers=None
            )

    def test_manager_rejects_invalid_provider(self):
        with self.assertRaises(GenerationError):
            LLMProviderManager(
                providers=[
                    Mock()
                ]
            )

    def test_manager_rejects_non_string_prompt(self):
        provider = TestProvider(
            answer="Answer"
        )

        manager = LLMProviderManager(
            providers=[
                provider
            ]
        )

        with self.assertRaises(GenerationError):
            manager.generate(123)

        self.assertEqual(
            provider.calls,
            [],
        )

    def test_manager_rejects_empty_prompt(self):
        provider = TestProvider(
            answer="Answer"
        )

        manager = LLMProviderManager(
            providers=[
                provider
            ]
        )

        with self.assertRaises(GenerationError):
            manager.generate("   ")

        self.assertEqual(
            provider.calls,
            [],
        )


    def test_falls_back_after_unexpected_provider_exception(self):
        primary = TestProvider(
            error=RuntimeError(
                "Unexpected provider failure."
            )
        )
        secondary = TestProvider(
            answer="Secondary answer"
        )

        manager = LLMProviderManager(
            providers=[
                primary,
                secondary,
            ]
        )

        result = manager.generate(
            "Test prompt."
        )

        self.assertEqual(
            result,
            "Secondary answer",
        )

        self.assertEqual(
            primary.calls,
            ["Test prompt."],
        )

        self.assertEqual(
            secondary.calls,
            ["Test prompt."],
        )

    def test_falls_back_after_non_string_provider_response(self):
        primary = TestProvider(
            answer=123
        )
        secondary = TestProvider(
            answer="Secondary answer"
        )

        manager = LLMProviderManager(
            providers=[
                primary,
                secondary,
            ]
        )

        result = manager.generate(
            "Test prompt."
        )

        self.assertEqual(
            result,
            "Secondary answer",
        )

        self.assertEqual(
            primary.calls,
            ["Test prompt."],
        )

        self.assertEqual(
            secondary.calls,
            ["Test prompt."],
        )

    def test_falls_back_after_empty_provider_response(self):
        primary = TestProvider(
            answer="   "
        )
        secondary = TestProvider(
            answer="Secondary answer"
        )

        manager = LLMProviderManager(
            providers=[
                primary,
                secondary,
            ]
        )

        result = manager.generate(
            "Test prompt."
        )

        self.assertEqual(
            result,
            "Secondary answer",
        )

        self.assertEqual(
            primary.calls,
            ["Test prompt."],
        )

        self.assertEqual(
            secondary.calls,
            ["Test prompt."],
        )

    def test_all_providers_unexpected_failures_raise_safe_error(self):
        primary = TestProvider(
            error=RuntimeError(
                "Groq internal details."
            )
        )
        secondary = TestProvider(
            error=TimeoutError(
                "Gemini timeout details."
            )
        )
        fallback = TestProvider(
            error=ValueError(
                "Ollama internal details."
            )
        )

        manager = LLMProviderManager(
            providers=[
                primary,
                secondary,
                fallback,
            ]
        )

        with self.assertRaises(GenerationError) as context:
            manager.generate(
                "Test prompt."
            )

        self.assertEqual(
            str(context.exception),
            "All configured LLM providers failed.",
        )

        self.assertNotIn(
            "Groq internal details.",
            str(context.exception),
        )

        self.assertNotIn(
            "Gemini timeout details.",
            str(context.exception),
        )

        self.assertNotIn(
            "Ollama internal details.",
            str(context.exception),
        )