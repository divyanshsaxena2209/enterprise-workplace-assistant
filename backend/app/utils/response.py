"""
Standardized response builder utilities.

Use these helpers in routers to build consistent success/error response dicts.
"""

from typing import Any


def success_response(
    message: str = "Operation completed successfully.",
    data: Any = None,
) -> dict[str, Any]:
    """
    Build a standardized success response dict.

    Example output::

        {
          "success": true,
          "message": "Profile updated successfully.",
          "data": { ... }
        }
    """
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(
    message: str,
    error_code: str = "UNKNOWN_ERROR",
) -> dict[str, Any]:
    """
    Build a standardized error response dict.

    Typically used for inline error returns — prefer raising domain
    exceptions (app/core/exceptions.py) and letting the middleware handle them.

    Example output::

        {
          "success": false,
          "message": "A resource with the provided details already exists.",
          "error_code": "CONFLICT"
        }
    """
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
    }
