"""
Common response schemas used across all API endpoints.

Every API response — success or error — MUST use one of these models
to guarantee a consistent envelope for the frontend and API consumers.
"""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    """
    Standard success envelope.

    Example::

        {
          "success": true,
          "message": "Profile updated successfully.",
          "data": { ... }
        }
    """

    success: bool = True
    message: str = "Operation completed successfully."
    data: DataT | None = None

    model_config = {"arbitrary_types_allowed": True}


class ErrorResponse(BaseModel):
    """
    Standard error envelope — returned for all 4xx and 5xx responses.

    Example::

        {
          "success": false,
          "message": "A resource with the provided details already exists.",
          "error_code": "CONFLICT"
        }
    """

    success: bool = False
    message: str
    error_code: str = Field(
        default="UNKNOWN_ERROR",
        description="Machine-readable error identifier for client-side handling.",
        examples=["AUTHENTICATION_FAILED", "NOT_FOUND", "CONFLICT"],
    )


class PaginatedResponse(BaseModel, Generic[DataT]):
    """
    Paginated list response — for use in future list endpoints.

    Example::

        {
          "success": true,
          "message": "...",
          "data": [...],
          "total": 50,
          "page": 1,
          "page_size": 10
        }
    """

    success: bool = True
    message: str = "Items retrieved successfully."
    data: list[DataT] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10

    model_config = {"arbitrary_types_allowed": True}
