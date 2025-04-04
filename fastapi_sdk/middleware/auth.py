"""Authentication middleware for FastAPI SDK.

This module provides middleware to validate JWT tokens from Authorization header.
"""

import re
from typing import List, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from fastapi_sdk.security.oauth import decode_access_token


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT token from Authorization header."""

    def __init__(
        self,
        app,
        *,
        public_routes: List[str],
        auth_issuer: str,
        auth_client_id: str,
        env: str,
        test_private_key_path: Optional[str] = None,
        test_public_key_path: Optional[str] = None,
    ):
        """Initialize the middleware.

        Args:
            app: The FastAPI application
            public_routes: List of routes that don't require authentication
            auth_issuer: The issuer of the JWT tokens
            auth_client_id: The client ID for authentication
            env: The environment (e.g., "test", "prod")
            test_private_key_path: Path to private key for test environment
            test_public_key_path: Path to public key for test environment
        """
        super().__init__(app)
        self.public_routes = public_routes
        self.auth_issuer = auth_issuer
        self.auth_client_id = auth_client_id
        self.env = env
        self.test_private_key_path = test_private_key_path
        self.test_public_key_path = test_public_key_path

        # Compile regex patterns for public routes
        self.public_route_patterns = []
        for route in public_routes:
            # Convert glob pattern to regex pattern
            pattern = route.replace(".", r"\.").replace("*", ".*")
            self.public_route_patterns.append(re.compile(f"^{pattern}$"))

    async def dispatch(self, request: Request, call_next):
        """Process the request and validate the JWT token.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            The response from the next handler or an error response
        """
        # Check if the path matches any public route pattern
        path = request.url.path
        for pattern in self.public_route_patterns:
            if pattern.match(path):
                return await call_next(request)  # Allow public routes

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header.split(" ")[1]  # Extract token

        try:
            payload = decode_access_token(
                token,
                auth_issuer=self.auth_issuer,
                auth_client_id=self.auth_client_id,
                env=self.env,
                test_public_key_path=self.test_public_key_path,
            )
            request.state.claims = payload  # Attach user info to request state
        except ValueError as e:
            return JSONResponse(status_code=401, content={"detail": str(e)})

        return await call_next(request)
