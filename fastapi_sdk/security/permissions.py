"""Permission handling for FastAPI routes."""

import asyncio
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException, Request

from fastapi_sdk.utils.constants import ErrorCode


def require_permission(permission: str) -> Callable:
    """
    Decorator to require a specific permission for a route.

    Args:
        permission: The required permission in the format "model:action"
                   (e.g., "project:create", "project:read")

    Returns:
        A decorator function that checks for the required permission

    Raises:
        HTTPException: If the user doesn't have the required permission
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the request object from kwargs
            request: Optional[Request] = kwargs.get("request")
            if not request:
                # If no request in kwargs, try to find it in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "code": ErrorCode.INTERNAL_ERROR.value,
                        "message": "Request object not found in route parameters",
                    },
                )

            # Get claims from request state
            claims = getattr(request.state, "claims", {})
            if not claims:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": ErrorCode.NO_CLAIMS.value,
                        "message": "No claims found in request",
                    },
                )

            # Get user permissions from claims
            user_permissions: List[str] = claims.get("permissions", [])
            user_roles: List[str] = claims.get("roles", [])

            # Check if user has the required permission directly
            if permission in user_permissions:
                return await func(*args, **kwargs)

            # Check if user has a role that grants the permission
            # This is a simple implementation - you might want to add role-based permission mapping
            if "superuser" in user_roles:
                return await func(*args, **kwargs)

            raise HTTPException(
                status_code=403,
                detail={
                    "code": ErrorCode.PERMISSION_DENIED.value,
                    "message": f"Permission denied: {permission} required",
                },
            )

        return wrapper

    return decorator


def require_combined_permission(
    permission: str,
    custom_permission_func: Optional[Callable[[Request, Dict[str, Any]], bool]] = None,
    custom_permission_error_message: str = "Permission denied",
) -> Callable:
    """
    Decorator to require both standard permission AND custom permission check for a route.

    Args:
        permission: The required standard permission in the format "model:action"
        custom_permission_func: Optional custom permission function that takes (request, resource_data) and returns bool
        custom_permission_error_message: Custom error message to show when custom permission is denied

    Returns:
        A decorator function that checks for both permissions

    Raises:
        HTTPException: If either permission check fails
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the request object from kwargs
            request: Optional[Request] = kwargs.get("request")
            if not request:
                # If no request in kwargs, try to find it in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "code": ErrorCode.INTERNAL_ERROR.value,
                        "message": "Request object not found in route parameters",
                    },
                )

            # Get claims from request state
            claims = getattr(request.state, "claims", {})
            if not claims:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": ErrorCode.NO_CLAIMS.value,
                        "message": "No claims found in request",
                    },
                )

            # First, check standard permission
            user_permissions: List[str] = claims.get("permissions", [])
            user_roles: List[str] = claims.get("roles", [])

            # Check if user has the required permission directly
            if permission not in user_permissions:
                # Check if user has a role that grants the permission
                if "superuser" not in user_roles:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "code": ErrorCode.PERMISSION_DENIED.value,
                            "message": f"Permission denied: {permission} required",
                        },
                    )

            # Second, check custom permission if provided
            if custom_permission_func is not None:
                # Extract resource data from the route parameters
                resource_data = {}
                for key, value in kwargs.items():
                    if key not in ["request", "db"]:  # Skip FastAPI-specific parameters
                        resource_data[key] = value

                # Call the custom permission function
                result = custom_permission_func(request, resource_data)
                if asyncio.iscoroutine(result):
                    result = await result
                if not result:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "code": ErrorCode.PERMISSION_DENIED.value,
                            "message": custom_permission_error_message,
                        },
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
