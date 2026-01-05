"""Exception handlers for FastAPI to format responses consistently."""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi_sdk.utils.constants import ErrorCode
from fastapi_sdk.utils.dependencies import get_request_id
from fastapi_sdk.utils.response import create_error_response, create_single_error


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException and format according to standard response format.

    Args:
        request: The FastAPI request object
        exc: The HTTPException instance

    Returns:
        JSONResponse with standardized format
    """
    request_id = get_request_id(request)

    # Extract error code from detail if it's a dict, otherwise use default
    if isinstance(exc.detail, dict):
        # If it already has code and message, use them directly
        if "code" in exc.detail and "message" in exc.detail:
            errors = [
                create_single_error(
                    code=exc.detail["code"],
                    message=exc.detail["message"],
                    field=exc.detail.get("field"),
                )
            ]
        else:
            # Otherwise, treat the whole dict as error data
            errors = [create_single_error(**exc.detail)]
    elif isinstance(exc.detail, list):
        errors = [
            create_single_error(
                message=item.get("msg", str(item)),
                code=item.get("code", ErrorCode.ERROR.value),
                field=item.get("loc", [None])[-1] if item.get("loc") else None,
            )
            for item in exc.detail
        ]
    else:
        # Try to extract error code from common patterns
        detail_str = str(exc.detail)
        code = ErrorCode.ERROR
        if "Permission denied" in detail_str:
            code = ErrorCode.PERMISSION_DENIED
        elif "not found" in detail_str.lower():
            code = ErrorCode.NOT_FOUND
        elif "Invalid" in detail_str:
            code = ErrorCode.INVALID_INPUT
        elif "Missing" in detail_str:
            code = ErrorCode.MISSING_REQUIRED
        elif "expired" in detail_str.lower():
            code = ErrorCode.EXPIRED
        elif "signature" in detail_str.lower():
            code = ErrorCode.INVALID_SIGNATURE

        errors = [create_single_error(message=detail_str, code=code)]

    response = create_error_response(
        errors=errors,
        status_code=exc.status_code,
        request_id=request_id,
    )
    return JSONResponse(status_code=exc.status_code, content=response)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors and format according to standard response format.

    Args:
        request: The FastAPI request object
        exc: The RequestValidationError instance

    Returns:
        JSONResponse with standardized format
    """
    request_id = get_request_id(request)

    errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error.get("loc", []) if loc != "body")
        field = field_path if field_path else None

        # Map Pydantic error types to error codes
        error_type = error.get("type", "")
        code = ErrorCode.VALIDATION_ERROR
        if error_type == "value_error.missing":
            code = ErrorCode.MISSING_REQUIRED
        elif error_type == "type_error":
            code = ErrorCode.INVALID_TYPE
        elif "str" in error_type or "string" in error_type:
            code = ErrorCode.INVALID_FORMAT
        elif "int" in error_type or "integer" in error_type:
            code = ErrorCode.INVALID_TYPE
        elif "float" in error_type:
            code = ErrorCode.INVALID_TYPE
        elif "bool" in error_type or "boolean" in error_type:
            code = ErrorCode.INVALID_TYPE
        elif "enum" in error_type:
            code = ErrorCode.INVALID_VALUE
        elif "greater_than" in error_type or "less_than" in error_type:
            code = ErrorCode.OUT_OF_RANGE
        elif "regex" in error_type:
            code = ErrorCode.INVALID_FORMAT

        errors.append(
            create_single_error(
                message=error.get("msg", "Validation error"),
                code=code,
                field=field,
            )
        )

    # Extract the original request body to include in the error response
    original_body = None
    if hasattr(exc, "body"):
        original_body = exc.body

    response = create_error_response(
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=request_id,
        data=original_body,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response
    )


async def starlette_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTPException and format according to standard response format.

    Args:
        request: The FastAPI request object
        exc: The StarletteHTTPException instance

    Returns:
        JSONResponse with standardized format
    """
    request_id = get_request_id(request)

    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    errors = [create_single_error(message=detail, code=ErrorCode.ERROR)]

    response = create_error_response(
        errors=errors,
        status_code=exc.status_code,
        request_id=request_id,
    )
    return JSONResponse(status_code=exc.status_code, content=response)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app.

    Args:
        app: The FastAPI application instance
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
