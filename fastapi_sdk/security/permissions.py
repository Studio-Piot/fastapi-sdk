"""Permission handling for FastAPI routes."""

from functools import wraps
from typing import Callable, Dict, List, Optional

from fastapi import HTTPException, Request


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
                    detail="Request object not found in route parameters",
                )

            # Get claims from request state
            claims = getattr(request.state, "claims", {})
            if not claims:
                raise HTTPException(
                    status_code=403,
                    detail="No claims found in request",
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
                detail=f"Permission denied: {permission} required",
            )

        return wrapper

    return decorator
