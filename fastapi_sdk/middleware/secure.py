"""Secure middleware for enforcing HTTPS in production environments.

This middleware provides environment-aware HTTPS enforcement with support for
X-Forwarded-Proto headers (useful when behind proxies/load balancers).

Note: FastAPI provides HTTPSRedirectMiddleware, but it:
- Always enforces HTTPS (no environment-based conditional)
- Doesn't check X-Forwarded-Proto header (won't work behind proxies)
- Uses ASGI app wrapper pattern (not BaseHTTPMiddleware), so cannot be inherited

This custom middleware uses BaseHTTPMiddleware (the standard Starlette pattern)
and addresses both limitations above.

See: https://fastapi.tiangolo.com/advanced/middleware/#httpsredirectmiddleware
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


class EnforceHTTPSMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS in production environments.

    Unlike FastAPI's built-in HTTPSRedirectMiddleware, this middleware:
    - Only enforces HTTPS in production (allows HTTP in development)
    - Checks X-Forwarded-Proto header for proxy/load balancer compatibility
    - Works correctly when deployed behind reverse proxies (nginx, AWS ALB, etc.)

    See: https://fastapi.tiangolo.com/advanced/middleware/#httpsredirectmiddleware
    """

    def __init__(self, app, env: str = "development"):
        """Initialize the middleware.

        Args:
            app: The FastAPI application
            env: The environment name (default: "development")
                - "production": Enforces HTTPS
                - Other values: No HTTPS enforcement
        """
        super().__init__(app)
        self.env = env

    async def dispatch(self, request: Request, call_next):
        """Dispatch request with HTTPS enforcement in production.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            RedirectResponse if HTTP in production, otherwise proceeds normally
        """
        # Only enforce HTTPS in production
        if self.env == "production":
            # Check X-Forwarded-Proto header first (for proxy/load balancer scenarios)
            # Fall back to request URL scheme if header is not present
            proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            if proto != "https":
                url = request.url.replace(scheme="https")
                return RedirectResponse(url=str(url), status_code=307)
        return await call_next(request)
