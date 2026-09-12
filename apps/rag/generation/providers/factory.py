from ..exceptions import GenerationError
from .gemini import GeminiProvider
from .groq import GroqProvider
from .manager import LLMProviderManager
from .ollama import OllamaProvider


def get_llm_provider():
    """
    Build the LearnMetrics AI provider chain.

    Only successfully configured providers are included.
    Priority order:
        Groq → Gemini → Ollama
    """
    providers = []

    for provider_class in (
        GroqProvider,
        GeminiProvider,
        OllamaProvider,
    ):
        try:
            providers.append(provider_class())
        except GenerationError:
            continue

    if not providers:
        raise GenerationError(
            "No LLM providers are configured or available."
        )

    return LLMProviderManager(providers=providers)