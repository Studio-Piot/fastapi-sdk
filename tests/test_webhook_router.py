"""Tests for webhook router"""

import json
import time

import pytest
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from fastapi_sdk.security.webhook import generate_signature
from fastapi_sdk.webhook.handler import registry
from tests.config import settings


@registry.register("test.event")
async def handler(payload: dict):
    """Test handler"""
    return f"Test handler processed {payload}"


def create_webhook_request(
    payload: dict,
    secret: str = settings.WEBHOOK_SECRET,
    timestamp: int = None,
) -> tuple[dict, dict]:
    """Create a webhook request with proper headers and signature"""
    if not timestamp:
        timestamp = int(time.time())

    # Remove spaces in payload
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = generate_signature(secret, body)

    headers = {
        "X-Signature": signature,
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    return payload, headers


@pytest.mark.asyncio
async def test_webhook_success(client):
    """Test successful webhook processing"""
    payload = {
        "event": "account.created",
        "data": {"id": 1, "name": "test"},
    }
    data, headers = create_webhook_request(payload)

    response = client.post("/webhook", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "result": "Account created with data test",
    }


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    """Test webhook with invalid signature"""
    payload = {
        "event": "test.event",
        "data": {"id": 1},
    }
    data, headers = create_webhook_request(payload, secret="wrong-secret")

    response = client.post("/webhook", json=data, headers=headers)
    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Invalid signature"}


@pytest.mark.asyncio
async def test_webhook_expired_request(client):
    """Test webhook with expired timestamp"""
    payload = {
        "event": "test.event",
        "data": {"id": 1},
    }
    # Create a timestamp from 6 minutes ago (beyond max_age_seconds)
    timestamp = int(time.time()) - 360
    data, headers = create_webhook_request(payload, timestamp=timestamp)

    response = client.post("/webhook", json=data, headers=headers)
    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Request expired"}


@pytest.mark.asyncio
async def test_webhook_invalid_timestamp(client):
    """Test webhook with invalid timestamp format"""
    payload = {
        "event": "test.event",
        "data": {"id": 1},
    }
    data, headers = create_webhook_request(payload)
    headers["X-Timestamp"] = "not-a-number"

    response = client.post("/webhook", json=data, headers=headers)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "Invalid timestamp" in response.json()["detail"]


@pytest.mark.asyncio
async def test_webhook_missing_event(client):
    """Test webhook with missing event in payload"""
    payload = {
        "data": {"id": 1},
    }
    data, headers = create_webhook_request(payload)

    response = client.post("/webhook", json=data, headers=headers)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Missing event in payload"}


@pytest.mark.asyncio
async def test_webhook_unregistered_event(client):
    """Test webhook with unregistered event"""
    payload = {
        "event": "nonexistent.event",
        "data": {"id": 1},
    }
    data, headers = create_webhook_request(payload)

    response = client.post("/webhook", json=data, headers=headers)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "No handler registered for event: nonexistent.event"
    }


@pytest.mark.asyncio
async def test_webhook_missing_headers(client):
    """Test webhook with missing required headers"""
    payload = {
        "event": "test.event",
        "data": {"id": 1},
    }

    # Test missing X-Signature
    response = client.post(
        "/webhook",
        json=payload,
        headers={"X-Timestamp": str(int(time.time()))},
    )
    assert response.status_code == 422  # FastAPI validation error

    # Test missing X-Timestamp
    response = client.post(
        "/webhook",
        json=payload,
        headers={"X-Signature": "some-signature"},
    )
    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_webhook_custom_headers(client):
    """Test webhook with custom signature and timestamp header names"""

    # Test payload
    payload = {
        "event": "test.event",
        "data": {"id": 1, "name": "test"},
    }

    # Create request with custom headers
    timestamp = int(time.time())
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = generate_signature(settings.WEBHOOK_SECRET, body)

    headers = {
        "Revolut-Signature": signature,
        "Revolut-Request-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    # Test successful request with custom headers
    response = client.post("/custom-webhook", json=payload, headers=headers)
    assert response.status_code == 200
    assert "Test handler processed" in response.json()

    # Test that default headers don't work with custom router
    default_headers = {
        "X-Signature": signature,
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    response = client.post("/custom-webhook", json=payload, headers=default_headers)
    assert (
        response.status_code == 422
    )  # FastAPI validation error for missing custom headers


@pytest.mark.asyncio
async def test_webhook_multiple_signatures(client):
    """Test webhook with multiple signatures in Revolut format"""

    # Test payload
    payload = {
        "event": "test.event",
        "data": {"id": 1, "name": "test"},
    }

    # Create valid signature
    timestamp = int(time.time())
    body = json.dumps(payload, separators=(",", ":")).encode()
    valid_signature = generate_signature(settings.WEBHOOK_SECRET, body)

    # Create invalid signature (different secret)
    invalid_signature = generate_signature("wrong-secret", body)

    # Test single signature (v1= format)
    single_headers = {
        "X-Signature": f"v1={valid_signature}",
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    response = client.post("/webhook", json=payload, headers=single_headers)
    assert response.status_code == 200

    # Test single signature (v2= format)
    v2_headers = {
        "X-Signature": f"v2={valid_signature}",
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    response = client.post("/webhook", json=payload, headers=v2_headers)
    assert response.status_code == 200

    # Test single signature (custom key format)
    custom_headers = {
        "X-Signature": f"custom_key={valid_signature}",
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    response = client.post("/webhook", json=payload, headers=custom_headers)
    assert response.status_code == 200

    # Test multiple signatures with different keys
    multiple_headers = {
        "X-Signature": f"v1={invalid_signature},v2={valid_signature}",
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    response = client.post("/webhook", json=payload, headers=multiple_headers)
    assert response.status_code == 200

    # Test multiple signatures with all invalid
    invalid_multiple_headers = {
        "X-Signature": f"v1={invalid_signature},v2={invalid_signature}",
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    response = client.post("/webhook", json=payload, headers=invalid_multiple_headers)
    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Invalid signature"}

    # Test mixed format (plain, v1=, and v2=)
    mixed_headers = {
        "X-Signature": f"{invalid_signature},v1={invalid_signature},v2={valid_signature}",
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    response = client.post("/webhook", json=payload, headers=mixed_headers)
    assert response.status_code == 200
