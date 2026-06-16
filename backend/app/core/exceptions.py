"""
Custom exception classes for the Enterprise Workplace Assistant backend.

These exceptions are caught by the global error middleware and converted
into standardized ErrorResponse JSON objects. Never raise raw HTTPException
from services or repositories — raise these domain exceptions instead.
"""

from fastapi import status


class AppException(Exception):
    """Base class for all application exceptions."""

    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, error_code: str | None = None):
        self.message = message or self.__class__.message
        self.error_code = error_code or self.__class__.error_code
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# 4xx Client Errors
# ---------------------------------------------------------------------------


class AuthenticationError(AppException):
    """Raised when JWT is missing, expired, or invalid."""

    http_status = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_FAILED"
    message = "Authentication required. Please provide a valid token."


class AuthorizationError(AppException):
    """Raised when a user lacks the required role/permission."""

    http_status = status.HTTP_403_FORBIDDEN
    error_code = "AUTHORIZATION_FAILED"
    message = "You do not have permission to perform this action."


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    http_status = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class ConflictError(AppException):
    """Raised when an operation would create a duplicate resource."""

    http_status = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"
    message = "A resource with the provided details already exists."


class ValidationError(AppException):
    """Raised when business-level validation fails (beyond Pydantic)."""

    http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"
    message = "The provided data failed validation."


class BadRequestError(AppException):
    """Raised for malformed or logically invalid requests."""

    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"
    message = "The request could not be processed."


# ---------------------------------------------------------------------------
# 5xx Server Errors
# ---------------------------------------------------------------------------


class ServiceUnavailableError(AppException):
    """Raised when an external dependency (Supabase, AI) is unreachable."""

    http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"
    message = "A downstream service is temporarily unavailable."


class DatabaseError(AppException):
    """Raised when a database operation fails unexpectedly."""

    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "DATABASE_ERROR"
    message = "A database error occurred. Please try again."
