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

# For providers with custom header names (e.g., Revolut)
revolut_webhook_router = create_webhook_router(
    webhook_secret="your-revolut-secret-key",
    prefix="/api/webhooks/revolut",
    signature_header="Revolut-Signature",
    timestamp_header="Revolut-Request-Timestamp",
    tags=["revolut-webhooks"]
)

# Include the routers in your app
app.include_router(webhook_router)
app.include_router(revolut_webhook_router)
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

## Custom Header Names

Some webhook providers use different header names for signatures and timestamps. You can configure custom header names when creating your webhook router:

```python
# Default headers (X-Signature, X-Timestamp)
default_webhook_router = create_webhook_router(
    webhook_secret="your-secret-key"
)

# Revolut webhook headers
revolut_webhook_router = create_webhook_router(
    webhook_secret="your-revolut-secret",
    signature_header="Revolut-Signature",
    timestamp_header="Revolut-Request-Timestamp"
)

# Any custom headers
custom_webhook_router = create_webhook_router(
    webhook_secret="your-secret-key",
    signature_header="Custom-Signature-Header",
    timestamp_header="Custom-Timestamp-Header"
)
```

## Multiple Signatures

Some providers support multiple signatures in a single header, separated by commas. This is useful when multiple signing secrets are active during key rotation. The webhook system automatically handles various signature formats:

```python
# Single signature (standard format)
"X-Signature": "4fce70bda66b2e713be09fbb7ab1b31b0c8976ea4eeb01b244db7b99aa6482cb"

# Multiple signatures with versioned keys
"Revolut-Signature": "v1=4fce70bda66b2e713be09fbb7ab1b31b0c8976ea4eeb01b244db7b99aa6482cb,v2=6ffbb59b2300aae63f272406069a9788598b792a944a07aba816edb039989a39"

# Mixed format (plain, v1=, v2=, custom keys)
"X-Signature": "4fce70bda66b2e713be09fbb7ab1b31b0c8976ea4eeb01b244db7b99aa6482cb,v1=6ffbb59b2300aae63f272406069a9788598b792a944a07aba816edb039989a39,custom_key=7ffbb59b2300aae63f272406069a9788598b792a944a07aba816edb039989a40"

# Different key formats
"X-Signature": "v1=signature1,v2=signature2,api_key=signature3,version=signature4"
```

The system will:
- Split multiple signatures by comma
- Try each signature until one validates successfully
- Support any `key=` format (automatically strips the prefix)
- Support plain signatures without prefixes
- Return `403 Forbidden` only if all signatures fail validation

## Timestamp Formats

The webhook system automatically detects and handles different timestamp formats:

- **Seconds (10 digits)**: `1640995200` - Standard Unix timestamp
- **Milliseconds (13 digits)**: `1640995200000` - Millisecond precision timestamp

The system automatically converts milliseconds to seconds for internal processing, so both formats work seamlessly.

## Sending Webhooks

When sending webhooks to your endpoint, you need to include:

1. A valid signature in the configured signature header (default: `X-Signature`)
2. A timestamp in the configured timestamp header (default: `X-Timestamp`) - supports both seconds and milliseconds
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
    
    # Create headers (supports both seconds and milliseconds)
    timestamp = str(int(time.time()))  # Seconds format
    # timestamp = str(int(time.time() * 1000))  # Milliseconds format
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

# Example with milliseconds timestamp
def send_webhook_milliseconds(url: str, secret: str, event: str, data: dict):
    """Send webhook with millisecond timestamp"""
    payload = {
        "event": event,
        "data": data
    }
    
    # Use milliseconds timestamp (13 digits)
    timestamp = str(int(time.time() * 1000))
    body = json.dumps(payload, separators=(",", ":"))
    signature = generate_signature(secret, body.encode())
    
    headers = {
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Example with multiple signatures (generic key= format)
def send_multi_signature_webhook(url: str, secret: str, event: str, data: dict):
    """Send webhook with multiple signatures using different key formats"""
    payload = {
        "event": event,
        "data": data
    }
    
    timestamp = str(int(time.time()))
    body = json.dumps(payload, separators=(",", ":"))
    signature = generate_signature(secret, body.encode())
    
    # Create multiple signatures with different key formats
    signatures = [
        signature,  # Plain signature
        f"v1={signature}",  # Versioned signature
        f"v2={signature}",  # Different version
        f"api_key={signature}",  # Custom key format
    ]
    
    headers = {
        "X-Signature": ",".join(signatures),
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
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
- `signature_header` (str, optional): Header name for webhook signature (default: "X-Signature")
- `timestamp_header` (str, optional): Header name for request timestamp (default: "X-Timestamp")

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
