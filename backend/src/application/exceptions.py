"""Application layer exceptions."""


class ApplicationException(Exception):
    """Base exception for application layer."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class UseCaseException(ApplicationException):
    """Use case execution failed."""


class ValidationException(ApplicationException):
    """Validation failed."""
