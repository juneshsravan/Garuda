from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """Base application exception with standardized code, message, and details."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def format_error_response(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> dict:
    """Enforces standard error shape: { 'error': { 'code': '...', 'message': '...', 'details': {...} } }"""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Formats validation errors into field-level details."""
    field_details: Dict[str, list] = {}
    for err in exc.errors():
        # Clean field location e.g. body -> email
        loc_parts = [str(part) for part in err["loc"] if part not in ("body", "query", "path")]
        field = ".".join(loc_parts) if loc_parts else "non_field_errors"
        field_details.setdefault(field, []).append(err["msg"])

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed. Please check the provided fields.",
            details=field_details,
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = f"HTTP_{exc.status_code}"
    if exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=code,
            message=str(exc.detail),
            details={},
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred.",
            details={},
        ),
    )
