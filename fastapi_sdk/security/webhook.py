"""Webhook security utilities"""

import hashlib
import hmac
import re

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST


def generate_signature(secret: str, payload: bytes) -> str:
    """Generate a signature for the payload"""
    return hmac.new(
        key=secret.encode(), msg=payload, digestmod=hashlib.sha256
    ).hexdigest()


def verify_signature(secret: str, payload: bytes, signature: str) -> bool:
    """Verify the signature of the payload

    Supports both single signatures and multiple signatures:
    - Single: "4fce70bda66b2e713be09fbb7ab1b31b0c8976ea4eeb01b244db7b99aa6482cb"
    - Multiple: "v1=4fce70bda66b2e713be09fbb7ab1b31b0c8976ea4eeb01b244db7b99aa6482cb,v2=6ffbb59b2300aae63f272406069a9788598b792a944a07aba816edb039989a39"
    - Mixed: "4fce70bda66b2e713be09fbb7ab1b31b0c8976ea4eeb01b244db7b99aa6482cb,v1=6ffbb59b2300aae63f272406069a9788598b792a944a07aba816edb039989a39"
    """
    try:
        # Handle multiple signatures (Revolut format)
        if "," in signature:
            signatures = [s.strip() for s in signature.split(",")]
            for sig in signatures:
                if verify_single_signature(secret, payload, sig):
                    return True
            return False
        else:
            # Handle single signature
            return verify_single_signature(secret, payload, signature)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=f"Invalid signature: {e}"
        ) from e


def verify_single_signature(secret: str, payload: bytes, signature: str) -> bool:
    """Verify a single signature (handles both plain and key= format)"""
    try:
        # Handle key= prefix format (e.g., v1=, v2=, etc.)
        if "=" in signature:
            signature = signature.split("=", 1)[1]  # Remove "key=" prefix

        # Check signature length (SHA-256 produces 64 hex characters)
        if len(signature) != 64:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Invalid signature length: expected 64 characters, got {len(signature)}",
            )

        # Check if signature contains only valid hex characters
        if not re.match(r"^[0-9a-f]{64}$", signature):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Invalid signature: must contain only hexadecimal characters (0-9, a-f)",
            )

        computed = hmac.new(
            key=secret.encode(), msg=payload, digestmod=hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=f"Invalid signature: {e}"
        ) from e


def verify_revolut_signature(
    secret: str, payload: str, timestamp: str, signature: str
) -> bool:
    """Verify Revolut webhook signature using their specific format

    Revolut uses: v1.{timestamp}.{payload} as the message to sign
    Signature format: v1={hmac_sha256_hash}

    Args:
        secret: The webhook signing secret
        payload: The raw JSON payload as string
        timestamp: The Revolut-Request-Timestamp header value
        signature: The Revolut-Signature header value (may contain multiple signatures)

    Returns:
        bool: True if any signature is valid, False otherwise
    """
    try:
        # Handle multiple signatures (comma-separated)
        if "," in signature:
            signatures = [s.strip() for s in signature.split(",")]
            for sig in signatures:
                if verify_single_revolut_signature(secret, payload, timestamp, sig):
                    return True
            return False
        else:
            return verify_single_revolut_signature(
                secret, payload, timestamp, signature
            )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=f"Invalid Revolut signature: {e}"
        ) from e


def verify_single_revolut_signature(
    secret: str, payload: str, timestamp: str, signature: str
) -> bool:
    """Verify a single Revolut signature"""
    try:
        # Revolut signature format: v1={hash}
        if not signature.startswith("v1="):
            return False

        # Extract the hash part
        expected_hash = signature[3:]  # Remove "v1=" prefix

        # Check hash length (SHA-256 produces 64 hex characters)
        if len(expected_hash) != 64:
            return False

        # Check if hash contains only valid hex characters
        if not re.match(r"^[0-9a-f]{64}$", expected_hash):
            return False

        # Create the payload to sign: v1.{timestamp}.{payload}
        payload_to_sign = f"v1.{timestamp}.{payload}"

        # Compute HMAC-SHA256
        computed_hash = hmac.new(
            key=secret.encode(), msg=payload_to_sign.encode(), digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_hash, expected_hash)
    except (ValueError, TypeError, UnicodeError):
        return False
