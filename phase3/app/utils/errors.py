class Phase3Error(Exception):
    """Base error for Phase 3 failures."""


class ConfigurationError(Phase3Error):
    """Raised when required runtime configuration is missing."""


class ExternalServiceError(Phase3Error):
    """Raised when an external service call fails after retries."""


class StructuredOutputError(Phase3Error):
    """Raised when model output is not valid structured JSON."""

