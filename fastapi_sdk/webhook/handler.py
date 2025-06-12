"""Webhook handler system"""

from functools import wraps
from typing import Any, Callable, Dict, Optional

# Type for webhook event handlers
WebhookHandler = Callable[[Dict[str, Any]], Any]


class WebhookHandlerRegistry:
    """Registry for webhook event handlers"""

    def __init__(self):
        self._handlers: Dict[str, WebhookHandler] = {}

    def register(self, event: str) -> Callable[[WebhookHandler], WebhookHandler]:
        """Register a handler for a specific webhook event"""

        def decorator(handler: WebhookHandler) -> WebhookHandler:
            @wraps(handler)
            async def wrapper(payload: Dict[str, Any]) -> Any:
                return await handler(payload)

            self._handlers[event] = wrapper
            return wrapper

        return decorator

    def get_handler(self, event: str) -> Optional[WebhookHandler]:
        """Get the handler for a specific event"""
        return self._handlers.get(event)

    def handle_event(self, event: str, payload: Dict[str, Any]) -> Any:
        """Handle a webhook event with its payload"""
        handler = self.get_handler(event)
        if handler is None:
            raise ValueError(f"No handler registered for event: {event}")
        return handler(payload)


# Create a global registry instance
registry = WebhookHandlerRegistry()
