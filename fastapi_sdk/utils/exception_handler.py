"""Exception handlers for FastAPI to format responses consistently."""

import json
import logging
from typing import Any, Awaitable, Callable, Iterable, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.datastructures import FormData
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi_sdk.utils.constants import ErrorCode
from fastapi_sdk.utils.dependencies import get_request_id
from fastapi_sdk.utils.response import create_error_response, create_single_error

# Define the new constant to avoid deprecation warning
# HTTP_422_UNPROCESSABLE_ENTITY is deprecated in favor of HTTP_422_UNPROCESSABLE_CONTENT
HTTP_422_UNPROCESSABLE_CONTENT = 422

logger = logging.getLogger("fastapi_sdk.errors")

ExceptionHandler = Callable[[Request, Any], Awaitable[JSONResponse]]

# An HTTP error on a write echoes the submitted payload in `data` for these
# statuses, so the client can refill the form alongside the errors.
PAYLOAD_ECHO_STATUS_CODES = frozenset({400, 409, 422})
PAYLOAD_ECHO_METHODS = frozenset({"POST", "PUT", "PATCH"})

# Field names whose values are masked in debug logs of error responses.
# A key matches when it contains one of these, ignoring case, "_" and "-",
# so "password" also covers "new_password" and "passwordConfirmation".
DEFAULT_SENSITIVE_FIELDS = frozenset(
    {"password", "secret", "token", "api_key", "card_number", "cvv", "cvc"}
)


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
        data=await _echo_payload(request, exc.status_code),
    )
    return JSONResponse(status_code=exc.status_code, content=response)


def _serialize_body(body: Any) -> Any:
    """Convert a request body into a JSON-serializable value.

    Form bodies become a dict (repeated keys become lists, files become their
    filename) and raw bytes are decoded, so the payload can be echoed back.
    """
    if isinstance(body, FormData):
        result: dict[str, Any] = {}
        for key in body.keys():
            values = [
                value.filename if isinstance(value, UploadFile) else value
                for value in body.getlist(key)
            ]
            result[key] = values[0] if len(values) == 1 else values
        return result
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    return body


async def _read_request_body(request: Request) -> Any:
    """Read the submitted body back from the request, or None if unavailable."""
    content_type = request.headers.get("content-type", "")
    try:
        if content_type.startswith("application/json"):
            return await request.json()
        if content_type.startswith(
            ("multipart/form-data", "application/x-www-form-urlencoded")
        ):
            return _serialize_body(await request.form())
    except Exception:  # pylint: disable=broad-except
        return None
    return None


def _normalize_key(key: str) -> str:
    return key.lower().replace("_", "").replace("-", "")


def _mask_sensitive(body: Any, sensitive_fields: Iterable[str]) -> Any:
    """Mask the values of sensitive keys, recursing into dicts and lists."""
    fragments = [_normalize_key(field) for field in sensitive_fields]
    if not fragments:
        return body

    def mask(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: (
                    "***"
                    if isinstance(key, str)
                    and any(f in _normalize_key(key) for f in fragments)
                    else mask(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [mask(item) for item in value]
        return value

    return mask(body)


def _get_sensitive_fields(request: Request) -> Iterable[str]:
    return getattr(request.app.state, "sensitive_fields", DEFAULT_SENSITIVE_FIELDS)


async def _echo_payload(request: Request, status_code: int) -> Any:
    """Return the submitted body for a failed write with an echo status, else None."""
    if (
        status_code in PAYLOAD_ECHO_STATUS_CODES
        and request.method in PAYLOAD_ECHO_METHODS
    ):
        return await _read_request_body(request)
    return None


def _format_validation_errors(
    error_list: list[dict[str, Any]],
    request_id: Optional[str] = None,
    original_body: Any = None,
) -> JSONResponse:
    """Format Pydantic-style validation errors into a standardized JSON response."""
    errors = []
    for error in error_list:
        field_path = ".".join(str(loc) for loc in error.get("loc", []) if loc != "body")
        field = field_path if field_path else None

        # Map Pydantic error types to error codes
        error_type = error.get("type", "")
        code = ErrorCode.VALIDATION_ERROR
        if error_type == "missing":
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

    response = create_error_response(
        errors=errors,
        status_code=HTTP_422_UNPROCESSABLE_CONTENT,
        request_id=request_id,
        data=original_body,
    )
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_CONTENT, content=response)


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
    original_body = _serialize_body(getattr(exc, "body", None))
    return _format_validation_errors(exc.errors(), request_id, original_body)


async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic ValidationError and format according to standard response format.

    Args:
        request: The FastAPI request object
        exc: The ValidationError instance

    Returns:
        JSONResponse with standardized format
    """
    request_id = get_request_id(request)
    original_body = await _read_request_body(request)
    return _format_validation_errors(exc.errors(), request_id, original_body)


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
        data=await _echo_payload(request, exc.status_code),
    )
    return JSONResponse(status_code=exc.status_code, content=response)


def _with_debug_logging(handler: ExceptionHandler) -> ExceptionHandler:
    """Wrap an exception handler so it logs the response it returns.

    Sensitive values are masked in the log only; the response is unchanged.
    """

    async def wrapper(request: Request, exc: Any) -> JSONResponse:
        response = await handler(request, exc)
        body = json.dumps(
            _mask_sensitive(json.loads(response.body), _get_sensitive_fields(request)),
            indent=2,
        )
        logger.warning(
            "%s %s -> %s\n%s",
            request.method,
            request.url.path,
            response.status_code,
            body,
        )
        return response

    return wrapper


def register_exception_handlers(
    app: FastAPI,
    debug: bool = False,
    sensitive_fields: Optional[Iterable[str]] = None,
) -> None:
    """Register all exception handlers with the FastAPI app.

    Args:
        app: The FastAPI application instance
        debug: Log every error response to the ``fastapi_sdk.errors`` logger
            (method, path, status and the full JSON body). Keep off in production,
            as the body can include submitted payloads.
        sensitive_fields: Field names whose values are masked as ``"***"`` in the
            debug log. Responses are never masked. Replaces
            ``DEFAULT_SENSITIVE_FIELDS``; extend it with
            ``DEFAULT_SENSITIVE_FIELDS | {"iban"}``. Pass an empty set to log
            every value.
    """
    app.state.sensitive_fields = frozenset(
        DEFAULT_SENSITIVE_FIELDS if sensitive_fields is None else sensitive_fields
    )
    handlers: list[tuple[type[Exception], ExceptionHandler]] = [
        (HTTPException, http_exception_handler),
        (RequestValidationError, validation_exception_handler),
        (ValidationError, pydantic_validation_exception_handler),
        (StarletteHTTPException, starlette_exception_handler),
    ]
    for exc_class, handler in handlers:
        if debug:
            handler = _with_debug_logging(handler)
        app.add_exception_handler(exc_class, handler)
