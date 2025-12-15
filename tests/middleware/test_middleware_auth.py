"""Test authentication middleware."""

from datetime import timedelta

import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from fastapi_sdk.middleware.auth import AuthMiddleware
from fastapi_sdk.utils.constants import ErrorCode
from fastapi_sdk.utils.test import create_access_token
from tests.config import settings


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    app = FastAPI()
    return app


@pytest.fixture
def auth_middleware(app):
    """Create an AuthMiddleware instance with test configuration."""
    app.add_middleware(
        AuthMiddleware,
        public_routes=["/public", "/public/*", "/docs", "/openapi.json"],
        auth_issuer=settings.AUTH_ISSUER,
        auth_client_id=settings.AUTH_CLIENT_ID,
        env=settings.ENVIRONMENT,
        jwk_url=settings.JWK_URL,
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
    )


@pytest.fixture
def test_token():
    """Create a test JWT token."""
    return create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "tenant_id": settings.AUTH_CLIENT_ID,
            "account_id": "test-account",
            "iss": settings.AUTH_ISSUER,
        },
    )


def test_public_route(app, auth_middleware):
    """Test that public routes are accessible without authentication."""

    @app.get("/public")
    async def public_route():
        return {"detail": "public"}

    client = TestClient(app)
    response = client.get("/public")
    assert response.status_code == 200
    assert response.json() == {"detail": "public"}


def test_public_route_with_wildcard(app, auth_middleware):
    """Test that public routes with wildcards are accessible without authentication."""

    @app.get("/public/items")
    async def public_items_route():
        return {"detail": "public items"}

    @app.get("/public/users")
    async def public_users_route():
        return {"detail": "public users"}

    client = TestClient(app)
    response = client.get("/public/items")
    assert response.status_code == 200
    assert response.json() == {"detail": "public items"}

    response = client.get("/public/users")
    assert response.status_code == 200
    assert response.json() == {"detail": "public users"}


def test_protected_route_with_valid_token(app, auth_middleware, test_token):
    """Test that protected routes are accessible with a valid token."""

    @app.get("/protected")
    async def protected_route(request: Request):
        return {"claims": request.state.claims}

    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "sub" in response.json()["claims"]
    assert "account_id" in response.json()["claims"]


def test_protected_route_without_token(app, auth_middleware):
    """Test that protected routes return 401 without a token."""

    @app.get("/protected")
    async def protected_route():
        return {"detail": "protected"}

    client = TestClient(app)
    response = client.get("/protected")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["status"]["code"] == 401
    assert response_data["status"]["message"] == "Unauthorized"
    assert response_data["errors"][0]["code"] == ErrorCode.MISSING_AUTH_HEADER.value
    assert (
        response_data["errors"][0]["message"]
        == "Missing or invalid Authorization header"
    )


def test_protected_route_with_invalid_token(app, auth_middleware):
    """Test that protected routes return 401 with an invalid token."""

    @app.get("/protected")
    async def protected_route():
        return {"detail": "protected"}

    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_protected_route_with_malformed_header(app, auth_middleware):
    """Test that protected routes return 401 with a malformed Authorization header."""

    @app.get("/protected")
    async def protected_route():
        return {"detail": "protected"}

    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": "malformed-header"},
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["status"]["code"] == 401
    assert response_data["status"]["message"] == "Unauthorized"
    assert response_data["errors"][0]["code"] == ErrorCode.MISSING_AUTH_HEADER.value
    assert (
        response_data["errors"][0]["message"]
        == "Missing or invalid Authorization header"
    )


def test_protected_route_with_expired_token(app, auth_middleware):
    """Test that protected routes return 401 with TOKEN_EXPIRED error code for expired tokens."""

    @app.get("/protected")
    async def protected_route():
        return {"detail": "protected"}

    # Create an expired token
    expired_token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "account_id": "test-account",
            "iss": settings.AUTH_ISSUER,
            "tenant_id": settings.AUTH_CLIENT_ID,
        },
        expires_delta=timedelta(minutes=-1),  # Expired token
    )

    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["status"]["code"] == 401
    assert response_data["status"]["message"] == "Unauthorized"
    assert response_data["errors"][0]["code"] == ErrorCode.TOKEN_EXPIRED.value
    assert "Token has expired" in response_data["errors"][0]["message"]


def test_protected_route_with_wrong_issuer(app, auth_middleware):
    """Test that protected routes return 401 with a token from wrong issuer."""

    @app.get("/protected")
    async def protected_route():
        return {"detail": "protected"}

    # Create a token with wrong issuer
    wrong_issuer_token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "account_id": "test-account",
            "iss": "https://wrong-issuer.com/",
            "tenant_id": settings.AUTH_CLIENT_ID,
        },
    )

    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {wrong_issuer_token}"},
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["status"]["code"] == 401
    assert response_data["status"]["message"] == "Unauthorized"
    assert response_data["errors"][0]["code"] == ErrorCode.TOKEN_INVALID_CLAIM.value
    assert "Invalid token claim" in response_data["errors"][0]["message"]


def test_protected_route_with_wrong_client_id(app, auth_middleware):
    """Test that protected routes return 401 with TOKEN_VERIFICATION_FAILED error code for wrong client ID."""

    @app.get("/protected")
    async def protected_route():
        return {"detail": "protected"}

    # Create a token with wrong client ID
    wrong_client_token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "account_id": "test-account",
            "iss": settings.AUTH_ISSUER,
            "tenant_id": "wrong-client-id",
        },
    )

    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {wrong_client_token}"},
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["status"]["code"] == 401
    assert response_data["status"]["message"] == "Unauthorized"
    assert (
        response_data["errors"][0]["code"] == ErrorCode.TOKEN_VERIFICATION_FAILED.value
    )
    assert (
        "Token tenant_id does not match auth_client_id"
        in response_data["errors"][0]["message"]
    )


def test_protected_route_with_invalid_signature(app, auth_middleware):
    """Test that protected routes return 401 with TOKEN_INVALID_SIGNATURE error code for invalid signatures."""

    @app.get("/protected")
    async def protected_route():
        return {"detail": "protected"}

    # Create a valid token first
    token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "account_id": "test-account",
            "iss": settings.AUTH_ISSUER,
            "tenant_id": settings.AUTH_CLIENT_ID,
        },
    )

    # Corrupt the signature by modifying the last part of the token
    parts = token.split(".")
    corrupted_token = f"{parts[0]}.{parts[1]}.{parts[2][:-5]}XXXXX"

    client = TestClient(app)
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {corrupted_token}"},
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["status"]["code"] == 401
    assert response_data["status"]["message"] == "Unauthorized"
    assert response_data["errors"][0]["code"] == ErrorCode.TOKEN_INVALID_SIGNATURE.value
    assert "Invalid token signature" in response_data["errors"][0]["message"]
