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
    """Verify the signature of the payload"""
    try:
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
