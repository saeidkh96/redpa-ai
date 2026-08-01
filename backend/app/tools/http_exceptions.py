from __future__ import annotations


class ExternalToolHTTPError(Exception):
    """Base exception for outbound HTTP operations used by tools."""


class ExternalToolConfigurationError(ExternalToolHTTPError):
    """Raised when an external tool is not configured correctly."""


class ExternalToolValidationError(ExternalToolHTTPError):
    """Raised when a URL, host, payload, or response is invalid."""


class ExternalToolConnectionError(ExternalToolHTTPError):
    """Raised when an external service cannot be reached."""


class ExternalToolTimeoutError(ExternalToolHTTPError):
    """Raised when an external service exceeds the configured timeout."""


class ExternalToolResponseError(ExternalToolHTTPError):
    """Raised when an external service returns an unusable response."""
