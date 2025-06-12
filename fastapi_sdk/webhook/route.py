"""Webhook routes"""

import json
import logging
import time
from typing import Optional

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
) -> APIRouter:
    """Create a webhook router with the specified configuration.

    Args:
        webhook_secret: The secret key used to verify webhook signatures
        max_age_seconds: Maximum age of webhook requests in seconds (default: 300)
        prefix: The URL prefix for the webhook endpoint (default: "/webhook")
        tags: Optional list of tags for API documentation

    Returns:
        APIRouter: A configured FastAPI router for webhook handling
    """
    router = APIRouter(prefix=prefix, tags=tags or ["webhooks"])

    @router.post("")
    async def webhook(
        request: Request,
        x_signature: str = Header(..., alias="X-Signature"),
        x_timestamp: str = Header(..., alias="X-Timestamp"),
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

        # Convert payload to bytes
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
