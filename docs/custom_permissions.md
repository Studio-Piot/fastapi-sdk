# Custom Permission Functions

This document explains how to use custom permission functions with the FastAPI SDK RouteController to implement complex permission logic that goes beyond simple token-based permissions.

## Overview

The RouteController now supports **layered permission checking** that combines:
1. **Standard permission checks** (token-based permissions like `log:read`)
2. **Custom permission functions** (business logic, parent object checks, etc.)

This means you get both layers of security:
- Users must have the standard permission in their token
- **AND** they must pass your custom permission logic

The custom permission functions allow you to implement complex permission logic based on:
- Parent object properties (e.g., customer settings)
- Resource relationships
- Business logic conditions
- Any other custom criteria

## How Layered Permissions Work

When you provide a custom permission function, the system performs **both** checks:

1. **Standard Permission Check**: Verifies the user has the required permission in their JWT token (e.g., `log:read`)
2. **Custom Permission Check**: Runs your custom function to check business logic (e.g., customer settings)

**Both checks must pass** for the user to access the route.

### Example Flow:
```
User requests GET /logs/123
    ↓
1. Check: Does user have "log:read" permission in token? ✅
    ↓
2. Check: Does customer have temperature_testing enabled? ✅
    ↓
3. Allow access to route
```

If either check fails, the user gets a 403 Forbidden response.

## Basic Usage

### 1. Define Your Custom Permission Function

Create a function that takes a `Request` object and resource data, then returns `True` if permission is granted:

```python
from fastapi import Request
from typing import Dict, Any

async def check_temperature_testing_permission(request: Request, resource_data: Dict[str, Any]) -> bool:
    """
    Check if the customer has temperature testing enabled for log access.
    
    Args:
        request: FastAPI request object containing claims
        resource_data: Dictionary containing route parameters (e.g., resource_id, data)
    
    Returns:
        bool: True if permission is granted, False otherwise
    """
    # Get claims from the request
    claims = request.state.claims
    customer_id = claims.get("customer_id")
    
    if not customer_id:
        return False
    
    # Example: Check if customer has temperature testing enabled
    # You would implement your actual database query here
    customer = await get_customer_by_id(customer_id)
    if not customer:
        return False
    
    # Check the specific setting
    return customer.enable_temperature_testing
```

### 2. Use the Custom Permission Function in RouteController

```python
from fastapi_sdk.controllers import RouteController
from fastapi_sdk.controllers import LogController
from fastapi_sdk.schemas import LogResponse, LogCreate, LogUpdate

# Define your custom permission function
async def check_log_permission(request: Request, resource_data: Dict[str, Any]) -> bool:
    """Check if user can access logs based on customer settings."""
    claims = request.state.claims
    customer_id = claims.get("customer_id")
    
    if not customer_id:
        return False
    
    # Check customer's temperature testing setting
    customer = await get_customer_by_id(customer_id)
    return customer and customer.enable_temperature_testing

# Create the route controller with custom permission
log_routes = RouteController(
    prefix="/logs",
    tags=["Logs"],
    controller=LogController,
    get_db=get_db,
    schema_response=LogResponse,
    schema_response_paginated=LogResponsePaginated,
    schema_create=LogCreate,
    schema_update=LogUpdate,
    allowed_query_fields=["customer_id", "device_id", "timestamp"],
    allowed_order_fields=["timestamp", "temperature"],
    # Custom permission configuration
    # This will check BOTH "log:read" permission AND your custom function
    custom_permission_func=check_log_permission,
    custom_permission_error_message="Temperature testing not enabled for this customer"
)

# Include the router in your FastAPI app
app.include_router(log_routes.router)
```

## Advanced Examples

### Example 1: Parent Object Permission Check

```python
async def check_project_access_permission(request: Request, resource_data: Dict[str, Any]) -> bool:
    """Check if user can access project resources based on project settings."""
    claims = request.state.claims
    user_id = claims.get("user_id")
    project_id = claims.get("project_id")
    
    if not user_id or not project_id:
        return False
    
    # Get the project to check its settings
    project = await get_project_by_id(project_id)
    if not project:
        return False
    
    # Check if the project allows the specific action
    # This could be based on project type, settings, etc.
    return project.allow_resource_management
```

### Example 2: Resource-Specific Permission Check

```python
async def check_resource_ownership_permission(request: Request, resource_data: Dict[str, Any]) -> bool:
    """Check if user owns the specific resource being accessed."""
    claims = request.state.claims
    user_id = claims.get("user_id")
    resource_id = resource_data.get("resource_id")
    
    if not user_id or not resource_id:
        return False
    
    # Get the resource and check ownership
    resource = await get_resource_by_id(resource_id)
    if not resource:
        return False
    
    # Check if the user owns this specific resource
    return resource.owner_id == user_id
```

### Example 3: Complex Business Logic Permission

```python
async def check_subscription_permission(request: Request, resource_data: Dict[str, Any]) -> bool:
    """Check if user's subscription allows access to premium features."""
    claims = request.state.claims
    user_id = claims.get("user_id")
    
    if not user_id:
        return False
    
    # Get user's subscription details
    user = await get_user_by_id(user_id)
    if not user:
        return False
    
    # Check subscription status and features
    subscription = await get_subscription_by_user_id(user_id)
    if not subscription:
        return False
    
    # Check if subscription is active and has the required feature
    return (
        subscription.is_active and 
        subscription.plan in ["premium", "enterprise"] and
        subscription.features.get("advanced_analytics", False)
    )
```

## Error Handling

The custom permission function should handle errors gracefully:

```python
async def safe_permission_check(request: Request, resource_data: Dict[str, Any]) -> bool:
    """Safe permission check with error handling."""
    try:
        claims = request.state.claims
        if not claims:
            return False
        
        # Your permission logic here
        return await your_permission_logic(request, resource_data)
        
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Permission check failed: {e}")
        # Return False to deny access on errors
        return False
```

## Best Practices

1. **Keep functions focused**: Each permission function should check one specific type of permission
2. **Handle errors gracefully**: Always return `False` on errors to maintain security
3. **Use async/await**: Permission checks often require database queries
4. **Cache when possible**: Consider caching frequently accessed data like user settings
5. **Log permission failures**: Log failed permission checks for security monitoring

## Migration from Standard Permissions

If you're migrating from standard permissions, you can gradually introduce custom permissions:

```python
# Before: Standard permission
log_routes = RouteController(
    prefix="/logs",
    tags=["Logs"],
    controller=LogController,
    get_db=get_db,
    schema_response=LogResponse,
    schema_response_paginated=LogResponsePaginated,
    # ... other parameters
)

# After: Custom permission
log_routes = RouteController(
    prefix="/logs",
    tags=["Logs"],
    controller=LogController,
    get_db=get_db,
    schema_response=LogResponse,
    schema_response_paginated=LogResponsePaginated,
    # ... other parameters
    custom_permission_func=check_log_permission,
    custom_permission_error_message="Access denied: insufficient permissions"
)
```

## Testing Custom Permissions

Test your custom permission functions:

```python
import pytest
from fastapi import Request
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_temperature_testing_permission():
    """Test the temperature testing permission function."""
    # Mock request with claims
    request = Mock()
    request.state.claims = {"customer_id": "123"}
    
    # Mock resource data
    resource_data = {"resource_id": "log_456"}
    
    # Mock the database call
    with patch('your_module.get_customer_by_id') as mock_get_customer:
        mock_customer = Mock()
        mock_customer.enable_temperature_testing = True
        mock_get_customer.return_value = mock_customer
        
        # Test the permission function
        result = await check_temperature_testing_permission(request, resource_data)
        assert result is True

@pytest.mark.asyncio
async def test_permission_denied():
    """Test permission denied scenario."""
    request = Mock()
    request.state.claims = {"customer_id": "123"}
    resource_data = {"resource_id": "log_456"}
    
    with patch('your_module.get_customer_by_id') as mock_get_customer:
        mock_customer = Mock()
        mock_customer.enable_temperature_testing = False
        mock_get_customer.return_value = mock_customer
        
        result = await check_temperature_testing_permission(request, resource_data)
        assert result is False
```

This approach provides maximum flexibility while requiring minimal changes to your existing codebase.
