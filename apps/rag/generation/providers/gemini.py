from google import genai

from ..config import get_gemini_api_key, get_gemini_model
from ..exceptions import GenerationError
from .base import LLMProvider


class GeminiProvider(LLMProvider):
    """
    Gemini implementation of the LearnMetrics AI LLM provider contract.
    """

    def __init__(self, *, api_key=None, model=None):
        self.api_key = (
            api_key if api_key is not None else get_gemini_api_key()
        )
        self.model = (
            model if model is not None else get_gemini_model()
        )

        if not self.api_key:
            raise GenerationError(
                "Gemini API key is not configured."
            )

        if not self.model:
            raise GenerationError(
                "Gemini model is not configured."
            )

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as exc:
            raise GenerationError(
                "Failed to initialize Gemini provider."
            ) from exc

    def generate(self, prompt):
        if not isinstance(prompt, str):
            raise GenerationError(
                "Generation prompt must be a string."
            )

        if not prompt.strip():
            raise GenerationError(
                "Generation prompt cannot be empty."
            )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as exc:
            raise GenerationError(
                "Gemini answer generation failed."
            ) from exc

        try:
            answer = response.text
        except (AttributeError, TypeError) as exc:
            raise GenerationError(
                "Gemini returned an invalid response."
            ) from exc

        if not isinstance(answer, str) or not answer.strip():
            raise GenerationError(
                "Gemini returned an empty answer."
            )

        return answer.strip()