from ..exceptions import GenerationError
from .base import LLMProvider


class LLMProviderManager(LLMProvider):
    """
    Tries configured LLM providers in priority order.

    Provider failures are handled by moving to the next
    available provider.
    """

    def __init__(self, providers):
        if providers is None:
            raise GenerationError(
                "LLM providers are required."
            )

        self.providers = list(providers)

        if not self.providers:
            raise GenerationError(
                "At least one LLM provider is required."
            )

        for provider in self.providers:
            if not isinstance(provider, LLMProvider):
                raise GenerationError(
                    "All providers must implement LLMProvider."
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

        failures = []

        for provider in self.providers:
            try:
                answer = provider.generate(prompt)

                if not isinstance(answer, str):
                    raise GenerationError(
                        "Provider returned an invalid answer."
                    )

                if not answer.strip():
                    raise GenerationError(
                        "Provider returned an empty answer."
                    )

                return answer.strip()

            except GenerationError as exc:
                failures.append(exc)

            except Exception as exc:
                failures.append(exc)

        raise GenerationError(
            "All configured LLM providers failed."
        ) from failures[-1]