import requests

from ..config import get_ollama_base_url, get_ollama_model
from ..exceptions import GenerationError
from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """
    Local Ollama implementation of the LearnMetrics AI
    LLM provider contract.
    """

    def __init__(self, *, base_url=None, model=None):
        self.base_url = (
            base_url
            if base_url is not None
            else get_ollama_base_url()
        ).rstrip("/")

        self.model = (
            model
            if model is not None
            else get_ollama_model()
        )

        if not self.base_url:
            raise GenerationError(
                "Ollama base URL is not configured."
            )

        if not self.model:
            raise GenerationError(
                "Ollama model is not configured."
            )

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
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise GenerationError(
                "Ollama answer generation failed."
            ) from exc

        try:
            data = response.json()
            answer = data["response"]
        except (ValueError, KeyError, TypeError) as exc:
            raise GenerationError(
                "Ollama returned an invalid response."
            ) from exc

        if not isinstance(answer, str) or not answer.strip():
            raise GenerationError(
                "Ollama returned an empty answer."
            )

        return answer.strip()