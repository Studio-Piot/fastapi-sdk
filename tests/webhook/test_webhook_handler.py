"""Tests for webhook handler system"""

import pytest

from fastapi_sdk.webhook.handler import WebhookHandlerRegistry, registry


@pytest.fixture
def handler_registry():
    """Create a fresh registry for each test"""
    return WebhookHandlerRegistry()


@pytest.mark.asyncio
async def test_register_handler(handler_registry):
    """Test registering a handler"""

    @handler_registry.register("test.event")
    async def test_handler(payload: dict):
        return {"processed": True, "data": payload}

    # Verify handler was registered
    handler = handler_registry.get_handler("test.event")
    assert handler is not None

    # Test handler execution
    payload = {"id": 1, "name": "test"}
    result = await handler(payload)
    assert result == {"processed": True, "data": payload}


@pytest.mark.asyncio
async def test_register_multiple_handlers(handler_registry):
    """Test registering multiple handlers for different events"""

    @handler_registry.register("event.1")
    async def handler1(payload: dict):
        return {"event": "1", "data": payload}

    @handler_registry.register("event.2")
    async def handler2(payload: dict):
        return {"event": "2", "data": payload}

    # Verify both handlers were registered
    assert handler_registry.get_handler("event.1") is not None
    assert handler_registry.get_handler("event.2") is not None

    # Test both handlers
    payload = {"id": 1}
    result1 = await handler_registry.handle_event("event.1", payload)
    result2 = await handler_registry.handle_event("event.2", payload)

    assert result1 == {"event": "1", "data": payload}
    assert result2 == {"event": "2", "data": payload}


@pytest.mark.asyncio
async def test_handler_not_found(handler_registry):
    """Test handling an unregistered event"""
    with pytest.raises(ValueError) as exc_info:
        await handler_registry.handle_event("nonexistent.event", {})

    assert str(exc_info.value) == "No handler registered for event: nonexistent.event"


@pytest.mark.asyncio
async def test_handler_overwrite(handler_registry):
    """Test overwriting an existing handler"""

    @handler_registry.register("test.event")
    async def handler1(payload: dict):
        return {"version": 1, "data": payload}

    @handler_registry.register("test.event")  # Overwrite previous handler
    async def handler2(payload: dict):
        return {"version": 2, "data": payload}

    # Verify only the second handler is active
    result = await handler_registry.handle_event("test.event", {"id": 1})
    assert result == {"version": 2, "data": {"id": 1}}


@pytest.mark.asyncio
async def test_handler_preserves_metadata(handler_registry):
    """Test that handler metadata (name, docstring) is preserved"""

    @handler_registry.register("test.event")
    async def test_handler(payload: dict):
        """Test handler docstring"""
        return {"processed": True}

    # Get the wrapped handler
    handler = handler_registry.get_handler("test.event")

    # Verify metadata is preserved
    assert handler.__name__ == "test_handler"
    assert handler.__doc__ == "Test handler docstring"


@pytest.mark.asyncio
async def test_global_registry():
    """Test the global registry instance"""

    # Register a handler on the global registry
    @registry.register("global.event")
    async def global_handler(payload: dict):
        return {"global": True, "data": payload}

    # Test the handler
    result = await registry.handle_event("global.event", {"id": 1})
    assert result == {"global": True, "data": {"id": 1}}


@pytest.mark.asyncio
async def test_handler_with_complex_payload(handler_registry):
    """Test handler with complex nested payload"""

    @handler_registry.register("complex.event")
    async def complex_handler(payload: dict):
        return {
            "processed": True,
            "nested": payload.get("nested", {}),
            "list": payload.get("list", []),
        }

    complex_payload = {
        "nested": {"field1": "value1", "field2": {"subfield": 123}},
        "list": [1, 2, 3],
        "simple": "value",
    }

    result = await handler_registry.handle_event("complex.event", complex_payload)
    assert result == {
        "processed": True,
        "nested": complex_payload["nested"],
        "list": complex_payload["list"],
    }


@pytest.mark.asyncio
async def test_handler_error_propagation(handler_registry):
    """Test that handler errors are properly propagated"""

    @handler_registry.register("error.event")
    async def error_handler(payload: dict):
        raise ValueError("Test error")

    with pytest.raises(ValueError) as exc_info:
        await handler_registry.handle_event("error.event", {})

    assert str(exc_info.value) == "Test error"
