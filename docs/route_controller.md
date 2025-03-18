# Route Controller

The Route Controller is a powerful base class for generating authenticated CRUD routes in FastAPI applications. It provides a standardized way to create RESTful endpoints with built-in authentication, pagination, and soft delete capabilities.

## Features

- Automatic CRUD route generation
- Built-in authentication support
- Pagination support
- Soft delete functionality
- Customizable response schemas
- Flexible route inclusion/exclusion
- Type-safe with Pydantic models

## Setup

### 1. Install Dependencies

```bash
pip install fastapi-sdk
```

### 2. Configure Authentication Middleware

The Route Controller requires authentication middleware to be set up. Here's how to configure it:

```python
from fastapi import FastAPI
from fastapi_sdk.middleware.auth import AuthMiddleware

app = FastAPI()

# Configure authentication middleware
app.add_middleware(
    AuthMiddleware,
    public_routes=["/docs", "/redoc", "/openapi.json"],  # Routes that don't require auth
    auth_issuer="https://your-auth-server.com",  # Your authentication server URL
    auth_client_id="your-client-id",  # Your client ID for authentication
    env="development",  # Environment: "development" or "production"
    test_private_key_path="path/to/private.pem",  # Path to private key for development
    test_public_key_path="path/to/public.pem",  # Path to public key for development
)
```

The middleware parameters are:
- `public_routes`: List of routes that don't require authentication
- `auth_issuer`: The URL of your authentication server
- `auth_client_id`: Your client ID for authentication
- `env`: The environment ("development" or "production")
- `test_private_key_path`: Path to private key for development environment
- `test_public_key_path`: Path to public key for development environment

### 3. Set Up Database Connection

The Route Controller requires a database connection. Here's an example using SQLAlchemy:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine
engine = create_async_engine("postgresql+asyncpg://user:password@localhost/dbname")

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

## Usage

### 1. Define Your Models

First, define your Pydantic models for request/response handling:

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AccountBase(BaseModel):
    name: str

class AccountCreate(AccountBase):
    pass

class AccountUpdate(AccountBase):
    name: Optional[str] = None

class AccountResponse(AccountBase):
    uuid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 2. Create Your Model Controller

Create a controller class that inherits from `ModelController`:

```python
from fastapi_sdk.controllers import ModelController

class AccountController(ModelController):
    """Controller for Account model."""
    
    async def create(self, data: dict) -> AccountResponse:
        # Implement create logic
        pass

    async def get(self, uuid: str) -> Optional[AccountResponse]:
        # Implement get logic
        pass

    async def list(self, query: Optional[list] = None) -> list[AccountResponse]:
        # Implement list logic
        pass

    async def update(self, uuid: str, data: dict) -> Optional[AccountResponse]:
        # Implement update logic
        pass

    async def delete(self, uuid: str) -> bool:
        # Implement delete logic
        pass
```

### 3. Set Up Routes

Create a Route Controller instance and include it in your FastAPI app:

```python
from fastapi_sdk.controllers.route import RouteController
from fastapi_sdk.utils.schema import BaseResponsePaginated

# Create route controller
account_routes = RouteController(
    prefix="/accounts",
    tags=["accounts"],
    controller=AccountController,
    get_db=get_db,
    schema_response=AccountResponse,
    schema_response_paginated=BaseResponsePaginated[AccountResponse],
    schema_create=AccountCreate,
    schema_update=AccountUpdate,
)

# Include routes in FastAPI app
app.include_router(account_routes.router)
```

## Available Routes

The Route Controller automatically generates the following endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/accounts/` | Create a new account |
| GET | `/accounts/{uuid}` | Get account by ID |
| GET | `/accounts/` | List all accounts (paginated) |
| PUT | `/accounts/{uuid}` | Update account |
| DELETE | `/accounts/{uuid}` | Soft delete account |
| GET | `/accounts/deleted/` | List deleted accounts (paginated) |

## Customization

### Route Selection

You can customize which routes are included using the `include_routes` parameter:

```python
account_routes = RouteController(
    # ... other parameters ...
    include_routes=["create", "get", "list"],  # Only include these routes
)
```

Available options:
- `"create"`: Create endpoint
- `"get"`: Get by ID endpoint
- `"list"`: List all endpoint
- `"update"`: Update endpoint
- `"delete"`: Delete endpoint
- `"list_deleted"`: List deleted endpoint

### Response Schemas

You can customize the response schemas for different operations:

```python
account_routes = RouteController(
    # ... other parameters ...
    schema_response=AccountResponse,  # Response for single item
    schema_response_paginated=BaseResponsePaginated[AccountResponse],  # Response for list
    schema_create=AccountCreate,  # Schema for creation
    schema_update=AccountUpdate,  # Schema for updates
)
```

## Authentication

All routes require authentication by default. The authentication token should be included in the request header:

```
Authorization: Bearer your-jwt-token
```

The token should contain the necessary claims for your application. The middleware will validate the token and make the claims available in `request.state.claims`.

## Error Handling

The Route Controller includes standard error handling:

- 401: Unauthorized (missing or invalid token)
- 404: Resource not found
- 422: Validation error (invalid request data)

## Best Practices

1. **Model Design**
   - Use Pydantic models for request/response validation
   - Include proper type hints
   - Use `from_attributes = True` in response models

2. **Controller Implementation**
   - Implement proper error handling
   - Use async/await for database operations
   - Validate input data before processing

3. **Route Configuration**
   - Use meaningful prefixes and tags
   - Include only necessary routes
   - Customize response schemas as needed

4. **Security**
   - Use HTTPS in production
   - Implement proper token validation
   - Set appropriate token expiration times

## Example

Here's a complete example of setting up a Route Controller:

```python
from fastapi import FastAPI
from fastapi_sdk.controllers.route import RouteController
from fastapi_sdk.middleware.auth import AuthMiddleware
from fastapi_sdk.utils.schema import BaseResponsePaginated
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Models
class AccountBase(BaseModel):
    name: str

class AccountCreate(AccountBase):
    pass

class AccountUpdate(AccountBase):
    name: Optional[str] = None

class AccountResponse(AccountBase):
    uuid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Controller
class AccountController(ModelController):
    async def create(self, data: dict) -> AccountResponse:
        # Implementation
        pass

    async def get(self, uuid: str) -> Optional[AccountResponse]:
        # Implementation
        pass

    async def list(self, query: Optional[list] = None) -> list[AccountResponse]:
        # Implementation
        pass

    async def update(self, uuid: str, data: dict) -> Optional[AccountResponse]:
        # Implementation
        pass

    async def delete(self, uuid: str) -> bool:
        # Implementation
        pass

# FastAPI app
app = FastAPI()

# Middleware
app.add_middleware(
    AuthMiddleware,
    secret_key="your-secret-key",
    algorithm="HS256",
    token_prefix="Bearer",
)

# Database
async def get_db():
    # Implementation
    pass

# Routes
account_routes = RouteController(
    prefix="/accounts",
    tags=["accounts"],
    controller=AccountController,
    get_db=get_db,
    schema_response=AccountResponse,
    schema_response_paginated=BaseResponsePaginated[AccountResponse],
    schema_create=AccountCreate,
    schema_update=AccountUpdate,
)

# Include routes
app.include_router(account_routes.router)
``` 