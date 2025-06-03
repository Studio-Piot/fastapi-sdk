import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


class EnforceHTTPSMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS in production
    """

    def __init__(self, app, env: str = "development"):
        """Initialize the middleware.

        Args:
            app: The FastAPI application
            env: The environment name (default: "development")
        """
        super().__init__(app)
        self.env = env

    async def dispatch(self, request: Request, call_next):
        # Only enforce HTTPS in production
        if self.env == "production":
            proto = request.headers.get("x-forwarded-proto", "http")
            if proto != "https":
                url = request.url.replace(scheme="https")
                return RedirectResponse(url=str(url))
        return await call_next(request)
