"""Secure middlewares: HTTPS enforcement and security headers.

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

from collections.abc import Mapping, Sequence

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}


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


class SecurityHeadersMiddleware:
    """
    Middleware adding best-practice security headers to every HTTP response.

    It is a pure ASGI middleware (not BaseHTTPMiddleware), so it also covers
    streaming responses and responses returned by other middlewares. Register
    it last so it runs outermost.

    A header the response already has is never overwritten, so a route can set
    its own Cache-Control or Content-Security-Policy.
    """

    def __init__(
        self,
        app: ASGIApp,
        headers: Mapping[str, str | None] | None = None,
        csp_exempt_paths: Sequence[str] = ("/docs", "/redoc"),
        csp_exempt_content_types: Sequence[str] = (),
    ):
        """Initialize the middleware.

        Args:
            app: The ASGI application
            headers: Headers merged over DEFAULT_SECURITY_HEADERS; a value of
                None removes that default
            csp_exempt_paths: Path prefixes that get no Content-Security-Policy
                (Swagger UI and ReDoc load scripts from a CDN)
            csp_exempt_content_types: Response content types that get no
                Content-Security-Policy, matched as a prefix and ignoring
                parameters such as charset, e.g. ("application/pdf",)
        """
        self.app = app
        merged: dict[str, str | None] = dict(DEFAULT_SECURITY_HEADERS)
        for name, value in (headers or {}).items():
            # Match defaults case-insensitively so overrides replace them
            existing = next((k for k in merged if k.lower() == name.lower()), name)
            merged[existing] = value
        self.headers = [(k, v) for k, v in merged.items() if v is not None]
        self.csp_exempt_paths = tuple(csp_exempt_paths)
        self.csp_exempt_content_types = tuple(
            t.lower() for t in csp_exempt_content_types
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        path_exempt = any(path.startswith(prefix) for prefix in self.csp_exempt_paths)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                content_type = (
                    headers.get("content-type", "").split(";")[0].strip().lower()
                )
                skip_csp = path_exempt or any(
                    content_type.startswith(t) for t in self.csp_exempt_content_types
                )
                for name, value in self.headers:
                    if skip_csp and name.lower() == "content-security-policy":
                        continue
                    if name not in headers:
                        headers.append(name, value)
            await send(message)

        await self.app(scope, receive, send_with_headers)
