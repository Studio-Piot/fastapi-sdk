"""Tests for the secure middleware."""

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fastapi_sdk.middleware.secure import EnforceHTTPSMiddleware
from tests.config import settings


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    app = FastAPI()
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def test_https_middleware_with_settings(app, client):
    """Test that HTTPS middleware works with settings from config."""
    # Add middleware using environment from settings
    app.add_middleware(EnforceHTTPSMiddleware, env=settings.ENVIRONMENT)

    # Make a request with http
    response = client.get("/", headers={"x-forwarded-proto": "http"})

    # Check behavior based on environment
    if settings.ENVIRONMENT == "production":
        assert response.status_code == 307  # Temporary redirect
        assert response.headers.get("location").startswith("https://")
    else:
        assert response.status_code == 404  # 404 because we haven't defined any routes
        assert not response.headers.get("location")  # No redirect
