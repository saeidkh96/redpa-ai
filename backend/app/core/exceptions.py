class ApplicationError(Exception):
    """Base exception for application-level errors."""


class LLMServiceError(ApplicationError):
    """Raised when the configured LLM service cannot complete a request."""


class LLMConnectionError(LLMServiceError):
    """Raised when the application cannot connect to the LLM service."""


class LLMTimeoutError(LLMServiceError):
    """Raised when the LLM service does not respond before the timeout."""


class LLMInvalidResponseError(LLMServiceError):
    """Raised when the LLM service returns an invalid response."""