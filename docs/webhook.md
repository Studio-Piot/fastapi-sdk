# Webhook System

The webhook system provides a secure way to handle incoming webhook events in your FastAPI application. It includes signature verification, timestamp validation, and a flexible event handling system.

## Features

- Secure webhook endpoint with signature verification
- Timestamp validation to prevent replay attacks
- Flexible event-based handler system
- Customizable URL prefix and API documentation tags
- Automatic request validation and error handling

## Setup

1. Create a webhook router in your FastAPI application:

```python
from fastapi import FastAPI
from fastapi_sdk.webhook.route import create_webhook_router

app = FastAPI()

# Create webhook router with your configuration
webhook_router = create_webhook_router(
    webhook_secret="your-secret-key",  # Required: Secret key for signature verification
    max_age_seconds=300,              # Optional: Maximum age of webhook requests (default: 300)
    prefix="/api/webhooks",           # Optional: URL prefix (default: "/webhook")
    tags=["webhooks", "api"],         # Optional: API documentation tags
)

# Include the router in your app
app.include_router(webhook_router)
```

2. Register event handlers:

```python
from fastapi_sdk.webhook.handler import registry

@registry.register("user.created")
async def handle_user_created(payload: dict):
    """Handle user.created event"""
    user_data = payload.get("data", {})
    # Process the event
    return {"status": "processed", "user_id": user_data.get("id")}

@registry.register("order.updated")
async def handle_order_updated(payload: dict):
    """Handle order.updated event"""
    order_data = payload.get("data", {})
    # Process the event
    return {"status": "processed", "order_id": order_data.get("id")}
```

## Sending Webhooks

When sending webhooks to your endpoint, you need to include:

1. A valid signature in the `X-Signature` header
2. A timestamp in the `X-Timestamp` header
3. A JSON payload with an `event` field

Example request:

```python
import json
import time
import requests
from fastapi_sdk.security.webhook import generate_signature

def send_webhook(url: str, secret: str, event: str, data: dict):
    # Prepare payload
    payload = {
        "event": event,
        "data": data
    }
    
    # Create headers
    timestamp = str(int(time.time()))
    body = json.dumps(payload, separators=(",", ":"))  # Remove spaces
    signature = generate_signature(secret, body.encode())
    
    headers = {
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    # Send request
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Example usage
result = send_webhook(
    url="https://your-api.com/api/webhooks",
    secret="your-secret-key",
    event="user.created",
    data={"id": 123, "name": "John Doe"}
)
```

## Security

The webhook system includes several security features:

1. **Signature Verification**: Each request must include a valid HMAC-SHA256 signature
2. **Timestamp Validation**: Requests are rejected if they're too old (default: 5 minutes)
3. **Event Validation**: Each payload must include a valid event name
4. **Error Handling**: Detailed error messages for debugging

## Error Handling

The webhook endpoint returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid payload or event
- `403 Forbidden`: Invalid signature or expired request
- `422 Unprocessable Entity`: Missing required headers

Example error response:
```json
{
    "detail": "Invalid signature"
}
```

## Best Practices

1. **Secret Management**:
   - Store your webhook secret securely
   - Use environment variables or a secure configuration system
   - Rotate secrets periodically

2. **Event Handling**:
   - Use descriptive event names (e.g., `resource.action`)
   - Include relevant data in the payload
   - Handle events asynchronously when possible

3. **Error Handling**:
   - Log failed webhook attempts
   - Implement retry mechanisms for failed events
   - Monitor webhook processing

4. **Testing**:
   - Test webhook handlers with various payloads
   - Verify signature generation and validation
   - Test error cases and edge conditions

## Example Implementation

Here's a complete example of setting up and using the webhook system:

```python
from fastapi import FastAPI
from fastapi_sdk.webhook.route import create_webhook_router
from fastapi_sdk.webhook.handler import registry

app = FastAPI()

# Create webhook router
webhook_router = create_webhook_router(
    webhook_secret="your-secret-key",
    max_age_seconds=300,
    prefix="/api/webhooks",
    tags=["webhooks"]
)
app.include_router(webhook_router)

# Register event handlers
@registry.register("user.created")
async def handle_user_created(payload: dict):
    user_data = payload.get("data", {})
    # Process user creation
    return {"status": "success", "user_id": user_data.get("id")}

@registry.register("order.updated")
async def handle_order_updated(payload: dict):
    order_data = payload.get("data", {})
    # Process order update
    return {"status": "success", "order_id": order_data.get("id")}
```

## API Reference

### `create_webhook_router`

Creates a FastAPI router for handling webhooks.

Parameters:
- `webhook_secret` (str): Secret key for signature verification
- `max_age_seconds` (int, optional): Maximum age of webhook requests (default: 300)
- `prefix` (str, optional): URL prefix (default: "/webhook")
- `tags` (list[str], optional): API documentation tags

### `registry.register`

Decorator for registering webhook event handlers.

Parameters:
- `event` (str): Event name to handle

### `generate_signature`

Generates a signature for webhook payloads.

Parameters:
- `secret` (str): Secret key
- `payload` (bytes): Request body

Returns:
- `str`: HMAC-SHA256 signature
