from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Common contract for all LearnMetrics AI
    answer-generation providers.
    """

    @abstractmethod
    def generate(self, prompt):
        """
        Generate an answer from the supplied prompt.
        """
        raise NotImplementedError