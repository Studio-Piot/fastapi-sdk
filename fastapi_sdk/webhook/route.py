"""Webhook routes"""

import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from fastapi_sdk.security.webhook import verify_signature
from fastapi_sdk.webhook.handler import registry


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
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail=f"Invalid timestamp: {e}"
            ) from e

        now = int(time.time())
        if abs(now - timestamp) > max_age_seconds:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Request expired"
            )

        body = await request.body()

        if not verify_signature(webhook_secret, body, x_signature):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Invalid signature"
            )

        # Parse and process payload
        payload = await request.json()
        event = payload.get("event")

        if not event:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="Missing event in payload"
            )

        try:
            return await registry.handle_event(event, payload)
        except ValueError as e:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return router
