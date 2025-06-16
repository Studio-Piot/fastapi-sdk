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
