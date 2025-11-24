"""FastAPI dependencies for the SDK."""

import uuid

from fastapi import Request


def get_request_id(request: Request) -> str:
    """Get or generate a request ID for tracing.

    This function can be used both as a regular function call and as a FastAPI dependency.

    Usage as a dependency:
        async def my_route(request_id: str = Depends(get_request_id)):
            ...

    Usage as a regular function:
        request_id = get_request_id(request)

    Args:
        request: The FastAPI request object

    Returns:
        Request ID string
    """
    # Check if request ID already exists in state
    if hasattr(request.state, "request_id"):
        return request.state.request_id

    # Check for X-Request-ID header
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        request.state.request_id = request_id
        return request_id

    # Generate new request ID
    request_id = f"req-{uuid.uuid4().hex[:8]}"
    request.state.request_id = request_id
    return request_id
