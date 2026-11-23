"""Tests for the secure middleware."""

import pytest
from fastapi import FastAPI, WebSocket
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.testclient import TestClient

from fastapi_sdk.middleware.secure import (
    EnforceHTTPSMiddleware,
    SecurityHeadersMiddleware,
)
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


DEFAULT_HEADERS = {
    "strict-transport-security": "max-age=63072000; includeSubDomains",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    "cache-control": "no-store",
}


def _secure_app(**kwargs) -> FastAPI:
    """App with a few routes and the security headers middleware."""
    app = FastAPI()

    @app.get("/json")
    def json_route():
        return {"ok": True}

    @app.get("/cached")
    def cached_route():
        return JSONResponse({"ok": True}, headers={"Cache-Control": "max-age=60"})

    @app.get("/stream")
    def stream_route():
        return StreamingResponse(iter([b"a", b"b"]), media_type="text/plain")

    @app.get("/pdf")
    def pdf_route():
        return StreamingResponse(
            iter([b"%PDF-1.4"]),
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"},
        )

    @app.get("/pdf-charset")
    def pdf_charset_route():
        return Response(
            b"%PDF-1.4", headers={"Content-Type": "application/pdf; charset=binary"}
        )

    @app.get("/empty")
    def empty_route():
        return Response(status_code=204)

    class RejectMiddleware(BaseHTTPMiddleware):
        """Returns a 401 for /private, like an auth middleware."""

        async def dispatch(self, request, call_next):
            if request.url.path == "/private":
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
            return await call_next(request)

    app.add_middleware(RejectMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, **kwargs)
    return app


def _assert_defaults(response, exclude=()):
    for name, value in DEFAULT_HEADERS.items():
        if name in exclude:
            assert name not in response.headers
        else:
            assert response.headers.get(name) == value, name


def test_security_headers_defaults_on_json():
    response = TestClient(_secure_app()).get("/json")
    assert response.status_code == 200
    _assert_defaults(response)


def test_security_headers_on_response_from_other_middleware():
    response = TestClient(_secure_app()).get("/private")
    assert response.status_code == 401
    _assert_defaults(response)


def test_security_headers_on_404_and_204():
    client = TestClient(_secure_app())
    _assert_defaults(client.get("/missing"))
    _assert_defaults(client.get("/empty"))


def test_security_headers_on_streaming_response():
    response = TestClient(_secure_app()).get("/stream")
    assert response.text == "ab"
    _assert_defaults(response)


def test_security_headers_on_head_and_options():
    client = TestClient(_secure_app())
    _assert_defaults(client.head("/json"))
    _assert_defaults(client.options("/json"))


def test_security_headers_keep_route_headers():
    response = TestClient(_secure_app()).get("/cached")
    assert response.headers["cache-control"] == "max-age=60"
    assert response.headers.get_list("cache-control") == ["max-age=60"]
    assert response.headers["x-frame-options"] == "DENY"


def test_security_headers_csp_exempt_paths():
    client = TestClient(_secure_app())
    response = client.get("/docs")
    assert response.status_code == 200
    _assert_defaults(response, exclude=("content-security-policy",))
    # The OpenAPI schema is JSON and keeps the CSP
    _assert_defaults(client.get("/openapi.json"))


def test_security_headers_csp_exempt_paths_custom():
    client = TestClient(_secure_app(csp_exempt_paths=("/json",)))
    _assert_defaults(client.get("/json"), exclude=("content-security-policy",))
    _assert_defaults(client.get("/docs"))


def test_security_headers_csp_exempt_content_types():
    client = TestClient(_secure_app(csp_exempt_content_types=("application/pdf",)))
    response = client.get("/pdf")
    assert response.headers["content-disposition"] == "inline"
    _assert_defaults(response, exclude=("content-security-policy",))
    _assert_defaults(client.get("/pdf-charset"), exclude=("content-security-policy",))
    _assert_defaults(client.get("/json"))


def test_security_headers_pdf_keeps_csp_by_default():
    _assert_defaults(TestClient(_secure_app()).get("/pdf"))


def test_security_headers_override_and_remove():
    client = TestClient(
        _secure_app(
            headers={
                "x-frame-options": "SAMEORIGIN",
                "Cache-Control": None,
                "Permissions-Policy": "camera=()",
            }
        )
    )
    response = client.get("/json")
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert response.headers.get_list("x-frame-options") == ["SAMEORIGIN"]
    assert response.headers["permissions-policy"] == "camera=()"
    assert "cache-control" not in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"


def test_security_headers_skip_lifespan_and_websocket():
    app = _secure_app()

    @app.websocket("/ws")
    async def ws_route(websocket: WebSocket):
        await websocket.accept()
        await websocket.send_text("hello")
        await websocket.close()

    # Entering the client runs the lifespan
    with TestClient(app) as client, client.websocket_connect("/ws") as websocket:
        assert websocket.receive_text() == "hello"
