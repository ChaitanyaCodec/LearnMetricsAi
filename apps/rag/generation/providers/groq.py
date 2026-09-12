from groq import Groq

from ..config import get_groq_api_key, get_groq_model
from ..exceptions import GenerationError
from .base import LLMProvider


class GroqProvider(LLMProvider):
    """
    Groq implementation of the LearnMetrics AI LLM provider contract.
    """

    def __init__(self, *, api_key=None, model=None):
        self.api_key = (
            api_key if api_key is not None else get_groq_api_key()
        )
        self.model = (
            model if model is not None else get_groq_model()
        )

        if not self.api_key:
            raise GenerationError(
                "Groq API key is not configured."
            )

        if not self.model:
            raise GenerationError(
                "Groq model is not configured."
            )

        try:
            self.client = Groq(api_key=self.api_key)
        except Exception as exc:
            raise GenerationError(
                "Failed to initialize Groq provider."
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
        except Exception as exc:
            raise GenerationError(
                "Groq answer generation failed."
            ) from exc

        try:
            answer = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise GenerationError(
                "Groq returned an invalid response."
            ) from exc

        if not isinstance(answer, str) or not answer.strip():
            raise GenerationError(
                "Groq returned an empty answer."
            )

        return answer.strip()