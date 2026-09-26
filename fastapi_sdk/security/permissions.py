"""Permission handling for FastAPI routes."""

import asyncio
from functools import wraps
from typing import Any, Callable, Dict, Iterable, Literal, Mapping, Optional

from fastapi import HTTPException, Request

from fastapi_sdk.utils.constants import ErrorCode

# A role mapped to "*" may call every permission. superuser is always that role.
Grant = frozenset[str] | Literal["*"]


class RolePermissions:
    """Role grants checked alongside permissions carried on the token.

    Token ``permissions`` still grant access on their own. This map adds
    grants for roles. It never writes those grants back onto the claims.
    """

    def __init__(
        self,
        grants: Optional[Mapping[str, Iterable[str] | Literal["*"]]] = None,
    ):
        self.grants: Dict[str, Grant] = {}
        if grants:
            for role, permissions in grants.items():
                if role == "superuser":
                    continue
                self.grant(role, permissions)
        self.grants["superuser"] = "*"

    def grant(self, role: str, permissions: Iterable[str] | Literal["*"]) -> None:
        if permissions == "*":
            self.grants[role] = "*"
            return
        self.grants[role] = frozenset(permissions)

    def allows(self, claims: Mapping[str, Any], permission: str) -> bool:
        token_permissions = claims.get("permissions") or []
        if permission in token_permissions:
            return True
        for role in claims.get("roles") or []:
            granted = self.grants.get(role)
            if granted == "*":
                return True
            if granted is not None and permission in granted:
                return True
        return False


_policy = RolePermissions()


def configure_role_permissions(
    grants: Optional[Mapping[str, Iterable[str] | Literal["*"]]] = None,
) -> None:
    """Install the role grants used by every permission check.

    Replaces any grants from a previous call. ``superuser`` stays a grant of
    every permission. The decoded token claims are left unchanged.
    """
    global _policy
    _policy = RolePermissions(grants)


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

            if _policy.allows(claims, permission):
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

            if not _policy.allows(claims, permission):
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
