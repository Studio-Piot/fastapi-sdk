# Middlewares

This document describes the middleware components available in the FastAPI SDK.

## Authentication Middleware

The `AuthMiddleware` provides JWT token validation and authentication for your FastAPI application.

### Features

- JWT token validation from Authorization header
- Public route support with glob pattern matching
- Environment-specific key handling
- Automatic claims attachment to request state

### Setup

```python
from fastapi import FastAPI
from fastapi_sdk.middleware.auth import AuthMiddleware

app = FastAPI()

# Define public routes that don't require authentication
public_routes = [
    "/health",
    "/docs",
    "/openapi.json",
    "/auth/*"  # All routes under /auth/
]

# Add the middleware
app.add_middleware(
    AuthMiddleware,
    public_routes=public_routes,
    auth_issuer="https://your-auth-server.com",
    auth_client_id="your-client-id",
    env="production",  # or "development", "test"
    # Optional: test keys for test environment
    test_private_key_path="path/to/private.key",
    test_public_key_path="path/to/public.key"
)
```

### Configuration

The middleware accepts the following parameters:

- `public_routes`: List of routes that don't require authentication
  - Supports glob patterns (e.g., `/auth/*`, `/public/**`)
  - Patterns are converted to regex for matching
- `auth_issuer`: The issuer of the JWT tokens
- `auth_client_id`: The client ID for authentication
- `env`: The environment name ("production", "development", "test")
- `test_private_key_path`: Path to private key for test environment
- `test_public_key_path`: Path to public key for test environment

### Usage

1. **Public Routes**
   - Define routes that don't require authentication
   - Use glob patterns for flexible matching
   - Example: `/health`, `/docs`, `/auth/*`

2. **Protected Routes**
   - All routes not in `public_routes` require authentication
   - Requests must include a valid JWT token
   - Token must be in the format: `Bearer <token>`

3. **Accessing Claims**
   - Validated claims are attached to `request.state.claims`
   - Access in your route handlers:
   ```python
   @app.get("/protected")
   async def protected_route(request: Request):
       claims = request.state.claims
       return {"user_id": claims["sub"]}
   ```

### Error Handling

The middleware returns appropriate error responses:

- 401 Unauthorized:
  - Missing Authorization header
  - Invalid token format
  - Invalid or expired token
  - Invalid token signature

## Secure Middleware

The `EnforceHTTPSMiddleware` ensures secure communication by enforcing HTTPS in production environments.

### Features

- Automatic HTTPS redirection in production
- Environment-aware behavior
- X-Forwarded-Proto header support
- No redirection in development

### Setup

```python
from fastapi import FastAPI
from fastapi_sdk.middleware.secure import EnforceHTTPSMiddleware

app = FastAPI()

# Add the middleware
app.add_middleware(
    EnforceHTTPSMiddleware,
    env="production"  # or "development"
)
```

### Configuration

The middleware accepts the following parameters:

- `env`: The environment name
  - "production": Enforces HTTPS
  - "development": No HTTPS enforcement

### Behavior

1. **Production Environment**
   - Redirects HTTP requests to HTTPS
   - Uses 307 Temporary Redirect
   - Preserves original URL path and query parameters
   - Checks X-Forwarded-Proto header

2. **Development Environment**
   - No HTTPS enforcement
   - Allows both HTTP and HTTPS
   - Useful for local development

### Usage with Settings

```python
from fastapi import FastAPI
from fastapi_sdk.middleware.secure import EnforceHTTPSMiddleware
from your_app.config import settings

app = FastAPI()

# Add middleware using environment from settings
app.add_middleware(
    EnforceHTTPSMiddleware,
    env=settings.ENVIRONMENT
)
```

### Best Practices

1. **Always use in production**
   - Ensures secure communication
   - Protects against man-in-the-middle attacks
   - Required for compliance standards

2. **Development setup**
   - Disable in development for easier testing
   - Use environment variables to control behavior
   - Consider using a reverse proxy for local HTTPS

3. **Deployment considerations**
   - Ensure your hosting provider supports HTTPS
   - Configure SSL certificates properly
   - Set up proper X-Forwarded-Proto headers in your proxy
