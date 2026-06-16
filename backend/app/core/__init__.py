"""app/core package — configuration, security, enumerations, exceptions."""
from app.core.config import settings
from app.core.enums import UserRole
from app.core.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConflictError,
    DatabaseError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)

__all__ = [
    "settings",
    "UserRole",
    "AppException",
    "AuthenticationError",
    "AuthorizationError",
    "BadRequestError",
    "ConflictError",
    "DatabaseError",
    "NotFoundError",
    "ServiceUnavailableError",
    "ValidationError",
]
