"""
Centralized error/exception handling for the FastAPI application.

All app exceptions are mapped to the standardized ErrorResponse JSON format.
Internal details are never leaked in production responses.

Registration::

    from app.middleware.error_middleware import register_exception_handlers
    register_exception_handlers(app)
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import AppException
from app.core.config import settings

logger = logging.getLogger(__name__)


def _error_body(message: str, error_code: str, success: bool = False) -> dict[str, Any]:
    return {"success": success, "message": message, "error_code": error_code}


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app instance."""

    
    
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.info(
            "AppException [%s] on %s %s: %s",
            exc.error_code,
            request.method,
            request.url.path,
            exc.message,
        )
        
        message = exc.message
        if "10053" in message or "10054" in message or "aborted by the software" in message:
            message = "Connection to the database was temporarily interrupted. Please refresh the page."
            
        return JSONResponse(
            status_code=exc.http_status,
            content=_error_body(message, exc.error_code),
        )

    
    
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        
        messages = []
        for error in exc.errors():
            loc = " → ".join(str(l) for l in error["loc"] if l != "body")
            msg = error["msg"]
            messages.append(f"{loc}: {msg}" if loc else msg)

        message = "; ".join(messages) if messages else "Request validation failed."
        logger.debug("Validation error on %s: %s", request.url.path, message)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(message, "VALIDATION_ERROR"),
        )

    
    
    
    @app.exception_handler(PydanticValidationError)
    async def pydantic_exception_handler(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        messages = [f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()]
        message = "; ".join(messages) if messages else "Data validation failed."
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(message, "VALIDATION_ERROR"),
        )

    
    
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception on %s %s", request.method, request.url.path
        )
        
        exc_str = str(exc)
        if "10053" in exc_str or "10054" in exc_str or "aborted by the software" in exc_str:
            message = "Connection to the database was temporarily interrupted. Please refresh the page."
        else:
            message = (
                exc_str
                if settings.is_development
                else "An internal server error occurred. Please try again later."
            )
            
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(message, "INTERNAL_ERROR"),
        )
