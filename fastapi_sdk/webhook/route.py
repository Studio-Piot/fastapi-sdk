"""Webhook routes"""

import json
import logging
import time
from typing import Callable, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from fastapi_sdk.security.webhook import verify_signature
from fastapi_sdk.webhook.handler import registry

# Configure logger
logger = logging.getLogger(__name__)


def create_webhook_router(
    *,
    webhook_secret: str,
    max_age_seconds: int = 300,  # 5 minutes default
    prefix: str = "/webhook",
    tags: Optional[list[str]] = None,
    signature_header: str = "X-Signature",
    timestamp_header: str = "X-Timestamp",
    signature_verifier: Optional[Callable[[str, str, str, str], bool]] = None,
) -> APIRouter:
    """Create a webhook router with the specified configuration.

    Args:
        webhook_secret: The secret key used to verify webhook signatures
        max_age_seconds: Maximum age of webhook requests in seconds (default: 300)
        prefix: The URL prefix for the webhook endpoint (default: "/webhook")
        tags: Optional list of tags for API documentation
        signature_header: The header name for the webhook signature (default: "X-Signature")
        timestamp_header: The header name for the request timestamp (default: "X-Timestamp")
        signature_verifier: Optional custom signature verification function.
            If provided, this function will be used instead of the default verification.
            Function signature: (secret: str, payload: str, timestamp: str, signature: str) -> bool

    Returns:
        APIRouter: A configured FastAPI router for webhook handling
    """
    router = APIRouter(prefix=prefix, tags=tags or ["webhooks"])

    @router.post("")
    async def webhook(
        request: Request,
        x_signature: str = Header(..., alias=signature_header),
        x_timestamp: str = Header(..., alias=timestamp_header),
    ):
        """Webhook endpoint"""
        try:
            timestamp = int(x_timestamp)
        except ValueError as e:
            logger.error(
                "Invalid timestamp format in webhook request",
                extra={
                    "timestamp": x_timestamp,
                    "error": str(e),
                    "headers": dict(request.headers),
                },
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail=f"Invalid timestamp: {e}"
            ) from e

        # Auto-detect timestamp format: seconds vs milliseconds
        # Unix timestamp in seconds: 10 digits (e.g., 1640995200)
        # Unix timestamp in milliseconds: 13 digits (e.g., 1640995200000)
        if len(x_timestamp) == 13:
            # Convert milliseconds to seconds
            timestamp = timestamp // 1000
            logger.debug(
                "Converted millisecond timestamp to seconds",
                extra={
                    "original": x_timestamp,
                    "converted": timestamp,
                },
            )
        elif len(x_timestamp) == 10:
            # Already in seconds, no conversion needed
            pass
        else:
            logger.warning(
                "Unexpected timestamp format",
                extra={
                    "timestamp": x_timestamp,
                    "length": len(x_timestamp),
                    "headers": dict(request.headers),
                },
            )

        now = int(time.time())
        if abs(now - timestamp) > max_age_seconds:
            logger.warning(
                "Webhook request expired",
                extra={
                    "timestamp": timestamp,
                    "now": now,
                    "max_age": max_age_seconds,
                    "headers": dict(request.headers),
                },
            )
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Request expired"
            )

        # Parse and process payload
        try:
            payload = await request.json()
        except Exception as e:
            logger.error(
                "Failed to parse webhook payload",
                extra={
                    "error": str(e),
                    "headers": dict(request.headers),
                },
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {e}",
            ) from e

        # Use custom signature verification if provided, otherwise use default
        if signature_verifier:
            payload_str = json.dumps(payload, separators=(",", ":"))
            if not signature_verifier(
                webhook_secret, payload_str, x_timestamp, x_signature
            ):
                logger.warning(
                    "Invalid webhook signature (custom verifier)",
                    extra={
                        "signature": x_signature,
                        "timestamp": x_timestamp,
                        "headers": dict(request.headers),
                    },
                )
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Invalid signature"
                )
        else:
            # Use standard signature verification
            payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
            if not verify_signature(webhook_secret, payload_bytes, x_signature):
                logger.warning(
                    "Invalid webhook signature",
                    extra={
                        "signature": x_signature,
                        "headers": dict(request.headers),
                    },
                )
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Invalid signature"
                )

        event = payload.get("event")

        if not event:
            logger.warning(
                "Missing event in webhook payload",
                extra={
                    "payload": payload,
                    "headers": dict(request.headers),
                },
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="Missing event in payload"
            )

        try:
            result = await registry.handle_event(event, payload)
            logger.info(
                "Webhook event processed successfully",
                extra={
                    "event": event,
                    "payload": payload,
                },
            )
            return result
        except ValueError as e:
            logger.error(
                "Failed to process webhook event",
                extra={
                    "event": event,
                    "payload": payload,
                    "error": str(e),
                    "headers": dict(request.headers),
                },
            )
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return router
