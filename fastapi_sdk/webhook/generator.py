"""
Webhook utilities

Example usage:

```python
result = send_webhook(
    url="https://your-api.com/api/webhooks",
    secret="your-secret-key",
    event="user.created",
    data={"id": 123, "name": "John Doe"},
)
```

"""

import json
import logging
import time

import requests

from fastapi_sdk.security.webhook import generate_signature

# Configure logging
logger = logging.getLogger(__name__)


def send_webhook(url: str, secret: str, event: str, data: dict, meta_data: dict = None):
    """
    Send a webhook to the given URL with the given secret and event.

    Args:
        url: The URL to send the webhook to.
        secret: The secret to use for the webhook.
        event: The event to send.
        data: The data to send with the webhook.
        meta_data: Optional metadata to include in the webhook.
    """
    try:
        # Prepare payload
        payload = {"event": event, "data": data}
        if meta_data:
            payload["meta_data"] = meta_data

        # Create headers
        timestamp = str(int(time.time()))
        body = json.dumps(payload, separators=(",", ":"))  # Remove spaces
        signature = generate_signature(secret, body.encode())

        headers = {
            "X-Signature": signature,
            "X-Timestamp": timestamp,
            "Content-Type": "application/json",
        }

        logger.info("Sending webhook to %s with event %s", url, event)
        logger.debug("Webhook payload: %s", payload)

        # Send request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for non-200 status codes

        logger.info("Webhook sent successfully to %s", url)
        return response.json()

    except requests.exceptions.Timeout:
        logger.error("Webhook timeout for URL %s", url)
        raise
    except requests.exceptions.RequestException as e:
        logger.error("Webhook request failed for URL %s: %s", url, str(e))
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to decode webhook response from %s: %s", url, str(e))
        raise
    except Exception as e:
        logger.error(
            "Unexpected error sending webhook to %s: %s", url, str(e), exc_info=True
        )
        raise
