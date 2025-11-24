"""Response formatting utilities for standardized API responses."""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from fastapi_sdk.utils.constants import ErrorCode


class ErrorDetail(BaseModel):
    """Error detail structure."""

    field: Optional[str] = None
    code: str
    message: str


class StandardResponse(BaseModel):
    """Standard response format for all API responses."""

    status: Dict[str, Union[int, str]]
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
    errors: Optional[List[ErrorDetail]] = None
    meta: Optional[Dict[str, Any]] = None


def get_status_message(status_code: int) -> str:
    """Get standard HTTP status message for a status code.

    Args:
        status_code: HTTP status code

    Returns:
        Standard status message
    """
    status_messages = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }
    return status_messages.get(status_code, "Unknown")


def create_success_response(
    data: Any,
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized success response.

    Args:
        data: The response data (dict, list, or model)
        status_code: HTTP status code (default: 200)
        meta: Optional metadata to include
        request_id: Optional request ID for tracing

    Returns:
        Formatted response dictionary
    """
    # Convert Pydantic models to dict if needed
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif hasattr(data, "dict"):
        data = data.dict()

    response_meta = {
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if request_id:
        response_meta["request_id"] = request_id
    if meta:
        response_meta.update(meta)

    return {
        "status": {
            "code": status_code,
            "message": get_status_message(status_code),
        },
        "data": data,
        "errors": None,
        "meta": response_meta,
    }


def create_error_response(
    errors: Union[str, List[ErrorDetail], List[Dict[str, Any]]],
    status_code: int = 400,
    request_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized error response.

    Args:
        errors: Error message string, or list of ErrorDetail objects/dicts
        status_code: HTTP status code (default: 400)
        request_id: Optional request ID for tracing
        meta: Optional metadata to include

    Returns:
        Formatted error response dictionary
    """
    # Convert string to ErrorDetail list
    if isinstance(errors, str):
        error_list = [
            ErrorDetail(
                code=ErrorCode.ERROR.value,
                message=errors,
            )
        ]
    elif isinstance(errors, list):
        error_list = []
        for error in errors:
            if isinstance(error, ErrorDetail):
                error_list.append(error)
            elif isinstance(error, dict):
                error_list.append(ErrorDetail(**error))
            elif isinstance(error, str):
                error_list.append(
                    ErrorDetail(code=ErrorCode.ERROR.value, message=error)
                )

    response_meta = {
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if request_id:
        response_meta["request_id"] = request_id
    if meta:
        response_meta.update(meta)

    return {
        "status": {
            "code": status_code,
            "message": get_status_message(status_code),
        },
        "data": None,
        "errors": [error.model_dump() for error in error_list],
        "meta": response_meta,
    }


def create_single_error(
    message: str,
    code: Union[str, ErrorCode] = ErrorCode.ERROR,
    field: Optional[str] = None,
) -> ErrorDetail:
    """Create a single error detail.

    Args:
        message: Human-readable error message
        code: Machine-readable error code (ErrorCode enum or string)
        field: Optional field name for validation errors

    Returns:
        ErrorDetail object
    """
    # Convert ErrorCode enum to string value if needed
    code_value = code.value if isinstance(code, ErrorCode) else code
    return ErrorDetail(field=field, code=code_value, message=message)
