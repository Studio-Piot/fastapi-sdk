"""Tests for webhook security functions"""

import pytest
from fastapi import HTTPException

from fastapi_sdk.security.webhook import generate_signature, verify_signature


def test_generate_signature():
    """Test signature generation"""
    secret = "test-secret"
    payload = b'{"event": "test", "data": {"id": 1}}'

    signature = generate_signature(secret, payload)

    # Signature should be a hex string
    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA-256 produces 64 hex characters
    assert all(c in "0123456789abcdef" for c in signature)


def test_generate_signature_consistency():
    """Test that the same input always produces the same signature"""
    secret = "test-secret"
    payload = b'{"event": "test", "data": {"id": 1}}'

    signature1 = generate_signature(secret, payload)
    signature2 = generate_signature(secret, payload)

    assert signature1 == signature2


def test_generate_signature_different_inputs():
    """Test that different inputs produce different signatures"""
    secret = "test-secret"
    payload1 = b'{"event": "test1"}'
    payload2 = b'{"event": "test2"}'

    signature1 = generate_signature(secret, payload1)
    signature2 = generate_signature(secret, payload2)

    assert signature1 != signature2


def test_verify_signature_valid():
    """Test signature verification with valid signature"""
    secret = "test-secret"
    payload = b'{"event": "test", "data": {"id": 1}}'

    signature = generate_signature(secret, payload)
    assert verify_signature(secret, payload, signature) is True


def test_verify_signature_invalid():
    """Test signature verification with invalid signature"""
    secret = "test-secret"
    payload = b'{"event": "test", "data": {"id": 1}}'

    # Generate valid signature but modify it
    signature = generate_signature(secret, payload)
    invalid_signature = signature[:-1] + ("0" if signature[-1] == "1" else "1")

    assert verify_signature(secret, payload, invalid_signature) is False


def test_verify_signature_wrong_secret():
    """Test signature verification with wrong secret"""
    secret = "test-secret"
    wrong_secret = "wrong-secret"
    payload = b'{"event": "test", "data": {"id": 1}}'

    signature = generate_signature(secret, payload)
    assert verify_signature(wrong_secret, payload, signature) is False


def test_verify_signature_empty_payload():
    """Test signature verification with empty payload"""
    secret = "test-secret"
    payload = b""

    signature = generate_signature(secret, payload)
    assert verify_signature(secret, payload, signature) is True


def test_verify_signature_invalid_encoding():
    """Test signature verification with invalid encoding"""
    secret = "test-secret"
    payload = b'{"event": "test", "data": {"id": 1}}'

    test_cases = [
        ("x" * 64, "non-hex characters"),
        ("G" * 64, "uppercase hex characters"),
        ("0" * 63 + "g", "invalid hex character at end"),
        ("g" + "0" * 63, "invalid hex character at start"),
        ("0" * 32 + "x" + "0" * 31, "invalid hex character in middle"),
    ]

    for invalid_signature, description in test_cases:
        with pytest.raises(HTTPException) as exc_info:
            verify_signature(secret, payload, invalid_signature)

        assert exc_info.value.status_code == 400
        assert (
            "Invalid signature: must contain only hexadecimal characters (0-9, a-f)"
            in str(exc_info.value.detail)
        ), f"Failed for case: {description}"


def test_verify_signature_wrong_length():
    """Test signature verification with wrong signature length"""
    secret = "test-secret"
    payload = b'{"event": "test", "data": {"id": 1}}'

    # Create a signature with wrong length
    invalid_signature = "a" * 32  # SHA-256 should be 64 characters

    with pytest.raises(HTTPException) as exc_info:
        verify_signature(secret, payload, invalid_signature)

    assert exc_info.value.status_code == 400
    assert "Invalid signature length: expected 64 characters, got 32" in str(
        exc_info.value.detail
    )
