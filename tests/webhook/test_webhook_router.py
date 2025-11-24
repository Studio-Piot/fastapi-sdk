"""Tests for webhook router"""

import hashlib
import hmac
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
async def test_webhook_revolut_headers(client):
    """Test webhook with custom signature and timestamp header names"""

    # Test payload
    payload = {
        "event": "ORDER_COMPLETED",
        "order_id": "9fc01989-3f61-4484-a5d9-ffe768531be9",
        "merchant_order_ext_ref": "Test #3928",
    }

    # Test with Revolut signature format (use current timestamp)
    timestamp = str(int(time.time() * 1000))  # Current timestamp in milliseconds
    payload_str = json.dumps(payload, separators=(",", ":"))

    # Create Revolut-style signature: v1.{timestamp}.{payload}
    payload_to_sign = f"v1.{timestamp}.{payload_str}"

    # Generate signature using HMAC-SHA256
    signature_hash = hmac.new(
        key=settings.WEBHOOK_SECRET.encode(),
        msg=payload_to_sign.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    revolut_signature = f"v1={signature_hash}"

    headers = {
        "Revolut-Signature": revolut_signature,
        "Revolut-Request-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    # Test successful request with custom headers
    response = client.post("/revolut-webhook", json=payload, headers=headers)
    assert response.status_code == 200
    assert (
        "Order completed with data 9fc01989-3f61-4484-a5d9-ffe768531be9"
        in response.json()["result"]
    )

    # Test that default headers don't work with custom router
    default_headers = {
        "X-Signature": revolut_signature,
        "X-Timestamp": str(timestamp),
        "Content-Type": "application/json",
    }

    response = client.post("/revolut-webhook", json=payload, headers=default_headers)
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


@pytest.mark.asyncio
async def test_webhook_timestamp_formats(client):
    """Test webhook with different timestamp formats (seconds vs milliseconds)"""
    payload = {
        "event": "test.event",
        "data": {"id": 1, "name": "test"},
    }

    # Test with seconds timestamp (10 digits)
    timestamp_seconds = int(time.time())
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = generate_signature(settings.WEBHOOK_SECRET, body)

    seconds_headers = {
        "X-Signature": signature,
        "X-Timestamp": str(timestamp_seconds),
        "Content-Type": "application/json",
    }

    response = client.post("/webhook", json=payload, headers=seconds_headers)
    assert response.status_code == 200

    # Test with milliseconds timestamp (13 digits)
    timestamp_milliseconds = int(time.time() * 1000)
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = generate_signature(settings.WEBHOOK_SECRET, body)

    milliseconds_headers = {
        "X-Signature": signature,
        "X-Timestamp": str(timestamp_milliseconds),
        "Content-Type": "application/json",
    }

    response = client.post("/webhook", json=payload, headers=milliseconds_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_revolut_signature(client):
    """Test webhook with Revolut signature verification"""

    # Test payload (must match Revolut format exactly)
    payload = {
        "event": "ORDER_COMPLETED",
        "order_id": "9fc01989-3f61-4484-a5d9-ffe768531be9",
        "merchant_order_ext_ref": "Test #3928",
    }

    # Test with Revolut signature format (use current timestamp)
    timestamp = str(int(time.time() * 1000))  # Current timestamp in milliseconds
    payload_str = json.dumps(payload, separators=(",", ":"))

    # Create Revolut-style signature: v1.{timestamp}.{payload}
    payload_to_sign = f"v1.{timestamp}.{payload_str}"

    # Generate signature using HMAC-SHA256
    signature_hash = hmac.new(
        key=settings.WEBHOOK_SECRET.encode(),
        msg=payload_to_sign.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    revolut_signature = f"v1={signature_hash}"

    revolut_headers = {
        "Revolut-Signature": revolut_signature,
        "Revolut-Request-Timestamp": timestamp,
        "Content-Type": "application/json",
    }

    # Test successful Revolut webhook
    response = client.post("/revolut-webhook", json=payload, headers=revolut_headers)
    print(response.json())
    assert response.status_code == 200

    # Test with multiple Revolut signatures
    multiple_signatures = f"{revolut_signature},{revolut_signature}"
    multiple_headers = {
        "Revolut-Signature": multiple_signatures,
        "Revolut-Request-Timestamp": timestamp,
        "Content-Type": "application/json",
    }

    response = client.post("/revolut-webhook", json=payload, headers=multiple_headers)
    assert response.status_code == 200

    # Test with invalid Revolut signature
    invalid_headers = {
        "Revolut-Signature": "v1=invalid_signature",
        "Revolut-Request-Timestamp": timestamp,
        "Content-Type": "application/json",
    }

    response = client.post("/revolut-webhook", json=payload, headers=invalid_headers)
    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Invalid signature"}
