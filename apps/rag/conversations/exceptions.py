class ConversationServiceError(Exception):
    """Base exception for conversation service failures."""


class ConversationNotFoundError(ConversationServiceError):
    """Raised when a conversation does not exist or is inaccessible."""


class ConversationValidationError(ConversationServiceError):
    """Raised when conversation input is invalid."""