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
"""Create a database instance to be used as a dependency."""

from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from fauthy.config import settings


async def get_db_engine():
    """Create a new MongoDB connection to be used as dependency."""
    client = AsyncIOMotorClient(settings.MONGO_DATABASE_URI)
    db_engine = AIOEngine(client=client, database=settings.MONGO_DATABASE_NAME)
    try:
        yield db_engine
    finally:
        client.close()
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
from fastapi_sdk.tests.controllers import Account as AccountController
from fastapi_sdk.tests.schemas import AccountResponse, AccountResponsePaginated, AccountCreate, AccountUpdate

# Create route controller
account_routes = RouteController(
    prefix="/accounts",
    tags=["accounts"],
    controller=AccountController,
    get_db=get_db,
    schema_response=AccountResponse,
    schema_response_paginated=AccountResponsePaginated,
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

### Including Related Objects

You can include related objects in both list and get endpoints using the `include` query parameter:

```python
# List accounts with their projects included
GET /accounts/?include=projects

# List projecta with multiple relations included
GET /projects/?include=projects&include=account

# Get a specific account with its projects included
GET /accounts/{uuid}?include=projects
```

#### Example Responses

```json
// GET /accounts/?include=projects
{
    "items": [
        {
            "uuid": "acc_123",
            "name": "Account 1",
            "projects": [
                {
                    "uuid": "proj_1",
                    "name": "Project 1",
                    "account_id": "acc_123"
                }
            ]
        }
    ],
    "total": 1,
    "page": 0,
    "pages": 1,
    "size": 1
}

// GET /accounts/{uuid}?include=projects
{
    "uuid": "acc_123",
    "name": "Account 1",
    "projects": [
        {
            "uuid": "proj_1",
            "name": "Project 1",
            "account_id": "acc_123"
        }
    ]
}
```

#### Best Practices for Using Include

1. **Performance**
   - Be mindful of the number of relations you include
   - Consider implementing pagination for large related collections
   - Use appropriate indexes on foreign key fields

2. **Error Handling**
   - Non-existent relations are silently ignored
   - Invalid relation names are skipped
   - The response will still include the main object even if relation loading fails

3. **Security**
   - Relations are filtered based on the same ownership rules as the main object
   - Users can only access related objects they have permission to view

4. **Caching**
   - Consider implementing caching for frequently accessed relations
   - Use appropriate cache invalidation strategies when related objects change

5. **Documentation**
   - Document available relations in your API documentation
   - Provide examples of common include patterns
   - Explain any performance implications of including specific relations

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

2. **Ownership Configuration**
   - Configure ownership rules for each model controller
   - Use the `OwnershipRule` class to define ownership relationships
   - Example:
     ```python
     class ProjectController(ModelController):
         ownership_rule = OwnershipRule(
             claim_field="account_id",  # Field in the JWT claims
             model_field="account_id",  # Field in the model
             allow_public=False,  # Whether to allow access without ownership
         )
     ```
   - The ownership rule ensures that users can only access records that belong to them
   - When creating new records, the ownership field is automatically set from the user's claims
   - Users get a 404 error when trying to access records they don't own
   - The `allow_public` parameter determines whether records without ownership can be accessed

3. **Controller Implementation**
   - Implement proper error handling
   - Use async/await for database operations
   - Validate input data before processing

4. **Route Configuration**
   - Use meaningful prefixes and tags
   - Include only necessary routes
   - Customize response schemas as needed

5. **Security**
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
    """Account controller."""

    model = AccountModel
    schema_create = AccountCreate
    schema_update = AccountUpdate
    schema_response = AccountResponse
    cascade_delete = True  # Will delete related projects and tasks
    ownership_rule = OwnershipRule(
        claim_field="account_id",
        model_field="uuid",
        allow_public=False,
    )

    relationships = {
        "projects": {
            "type": "one_to_many",
            "controller": "Project",
            "foreign_key": "account_id",
        }
    }

    # Define custom pipeline stages
    extra_pipeline = [
        {
            "$project": {
                "name": 1,
                "email": 1,
                "status": 1,
                "created_at": 1,
                "is_active": {"$eq": ["$status", "active"]}
            }
        }
    ]

    # The pipeline will be automatically applied to all list queries

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

## Permission System

The RouteController implements a permission-based access control system that requires specific permissions for each CRUD operation. The permissions are automatically generated based on the model name and the action being performed.

### Permission Format

Permissions follow the format `{model_name}:{action}`, where:
- `model_name` is the lowercase name of your model (e.g., "project", "account")
- `action` is one of: "create", "read", "update", "delete"

For example:
- `project:create` - Permission to create new projects
- `project:read` - Permission to view projects
- `project:update` - Permission to modify projects
- `project:delete` - Permission to delete projects

### User Claims

The permission system relies on user claims in the request. The claims should include:
- `permissions`: List of permission strings the user has
- `roles`: List of roles the user has

Example claims:
```json
{
    "account_id": "acc_123",
    "permissions": ["project:create", "project:read"],
    "roles": ["user"]
}
```

### Permission Checks

The system checks permissions in the following order:
1. First checks if the user has the specific permission (e.g., "project:create")
2. If not, checks if the user has an admin or superuser role
3. If neither condition is met, returns a 403 Forbidden error

### Route Permissions

Each route requires specific permissions:

| Route | Method | Permission Required |
|-------|---------|-------------------|
| Create | POST | `{model_name}:create` |
| Get | GET | `{model_name}:read` |
| List | GET | `{model_name}:read` |
| Update | PUT | `{model_name}:update` |
| Delete | DELETE | `{model_name}:delete` |
| List Deleted | GET | `{model_name}:read` |

### Example Usage

```python
from fastapi_sdk.controllers import RouteController
from fastapi_sdk.security.permissions import require_permission

# Create a route controller
route_controller = RouteController(
    prefix="/projects",
    tags=["projects"],
    controller=ProjectController,
    get_db=get_db,
    schema_response=ProjectResponse,
    schema_response_paginated=ProjectResponsePaginated,
    schema_create=ProjectCreate,
    schema_update=ProjectUpdate,
)

# The routes will automatically require the following permissions:
# POST /projects/ -> project:create
# GET /projects/{id} -> project:read
# GET /projects/ -> project:read
# PUT /projects/{id} -> project:update
# DELETE /projects/{id} -> project:delete
# GET /projects/deleted/ -> project:read
```

### Error Responses

When a user lacks the required permission, the API returns a 403 Forbidden response:

```json
{
    "detail": "Permission denied: project:create required"
}
```

### Best Practices

1. **Role-Based Access**: Use roles for broad access control and specific permissions for fine-grained control
2. **Superuser Override**: Superuser roles automatically get access to all operations
3. **Permission Naming**: Keep permission names consistent with your model names
4. **Documentation**: Document required permissions in your API documentation

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
    """Account controller."""

    model = AccountModel
    schema_create = AccountCreate
    schema_update = AccountUpdate
    schema_response = AccountResponse
    cascade_delete = True  # Will delete related projects and tasks
    ownership_rule = OwnershipRule(
        claim_field="account_id",
        model_field="uuid",
        allow_public=False,
    )

    relationships = {
        "projects": {
            "type": "one_to_many",
            "controller": "Project",
            "foreign_key": "account_id",
        }
    }

    # Define custom pipeline stages
    extra_pipeline = [
        {
            "$project": {
                "name": 1,
                "email": 1,
                "status": 1,
                "created_at": 1,
                "is_active": {"$eq": ["$status", "active"]}
            }
        }
    ]

    # The pipeline will be automatically applied to all list queries
```

## Query and Order Parameters

The RouteController supports flexible querying and ordering through URL parameters. You can configure which fields are allowed for querying and ordering when initializing the RouteController.

### Configuration

```python
account_routes = RouteController(
    prefix="/accounts",
    tags=["accounts"],
    controller=AccountController,
    get_db=get_db,
    schema_response=AccountResponse,
    schema_response_paginated=AccountResponsePaginated,
    schema_create=AccountCreate,
    schema_update=AccountUpdate,
    allowed_query_fields=["name", "email", "status"],  # Fields that can be queried
    allowed_order_fields=["created_at", "updated_at", "name"],  # Fields that can be ordered by
)
```

### Query Parameters

You can filter results using query parameters. The system supports:
- Exact matches: `?name=John` (matches exactly "John")
- Contains matches (case-insensitive): `?name=*John*` (matches "John", "JOHN", "Johnson", etc.)
- Multiple values: `?status=active,pending`
- Range queries: `?created_at=2023-01-01..2023-12-31`
- Custom page size: `?n_per_page=50` (number of items per page, max 250)

Example:
```python
# List accounts with exact name match
GET /accounts/?name=John

# List accounts with name containing "john" (case-insensitive)
GET /accounts/?name=*john*

# List accounts with specific status
GET /accounts/?status=active,pending

# List accounts created in a date range
GET /accounts/?created_at=2023-01-01..2023-12-31

# List accounts with custom page size
GET /accounts/?n_per_page=50  # Get 50 items per page
```

### Pagination Parameters

The RouteController supports several pagination parameters:

1. **Page Size (`n_per_page`)**
   - Controls the number of items per page
   - Default value is 25
   - Maximum value is 250
   - Example: `GET /accounts/?n_per_page=50`

2. **Page Number (`page`)**
   - Zero-based page number
   - Example: `GET /accounts/?page=1` (second page)

3. **Combining Parameters**
   ```python
   # Get second page with 50 items per page
   GET /accounts/?page=1&n_per_page=50
   ```

The response includes pagination metadata:
```json
{
    "items": [...],
    "total": 100,    // Total number of items
    "page": 1,       // Current page number
    "pages": 2,      // Total number of pages
    "size": 50       // Number of items in current page
}
```

### Query Syntax

1. **Exact Match (Default)**
   - Just provide the value without special characters
   - Example: `?name=John` will only match "John"
   - Useful for fields like status, type, or other enum-like values

2. **Contains Match**
   - Use `*value*` syntax for contains matches
   - Example: `?name=*john*` will match "John", "Johnson", "Johnny", etc.
   - Case-insensitive by default
   - Good for text search and fuzzy matching

3. **Multiple Values**
   - Use comma-separated values
   - Example: `?status=active,pending`
   - Matches any of the provided values

4. **Range Queries**
   - Use `start..end` syntax
   - Example: `?created_at=2023-01-01..2023-12-31`
   - Works with dates, numbers, and other comparable values

### Order Parameters

You can order results using the `order_by` and `order_direction` parameters:
- `order_by`: Field to sort by (must be in allowed_order_fields)
- `order_direction`: Sort direction ("asc" or "desc")

Example:
```python
# List accounts ordered by creation date (newest first)
GET /accounts/?order_by=created_at&order_direction=desc

# List accounts ordered by name (alphabetically)
GET /accounts/?order_by=name&order_direction=asc
```

#### Ordering by Related Collections

You can also order by fields from related collections by using dot notation. To do this:
1. The related collection must be included in the `include` parameter
2. The field must be in the `allowed_order_fields` list
3. Use dot notation to specify the field (e.g., `project.name`)

Example:
```python
# List tasks ordered by their project's name
GET /tasks/?order_by=project.name&include=project&order_direction=asc

# List projects ordered by their account's name
GET /projects/?order_by=account.name&include=account&order_direction=desc
```

Note: When ordering by related collections:
- The related collection must be included in the `include` parameter
- The ordering is done after the related collections are loaded
- Performance may be affected when ordering by related collections with large datasets

### Combining Parameters

You can combine query and order parameters:

```python
# List active accounts ordered by creation date
GET /accounts/?status=active&order_by=created_at&order_direction=desc

# List accounts with name containing "john" and specific status
GET /accounts/?name=john&status=active,pending
```

### Error Handling

The system will return appropriate error responses:
- 400 Bad Request if querying on non-allowed fields
- 400 Bad Request if ordering by non-allowed fields
- 400 Bad Request if invalid order direction
- 400 Bad Request if invalid date range format

## Custom Pipeline

You can define custom MongoDB aggregation pipeline stages directly in your ModelController class. This allows you to add custom transformations and aggregations to your queries without exposing them through the API.

Example:
```python
class AccountController(ModelController):
    """Account controller."""

    model = AccountModel
    schema_create = AccountCreate
    schema_update = AccountUpdate
    schema_response = AccountResponse

    # Define custom pipeline stages
    extra_pipeline = [
        {
            "$project": {
                "name": 1,
                "email": 1,
                "status": 1,
                "created_at": 1,
                "is_active": {"$eq": ["$status", "active"]}
            }
        }
    ]

    # The pipeline will be automatically applied to all list queries
```

#### Pipeline Stage Examples

1. **Projection and Field Selection**
   ```python
   extra_pipeline = [
       {
           "$project": {
               "name": 1,
               "email": 1,
               "status": 1,
               "created_at": 1,
               "is_active": {"$eq": ["$status", "active"]}
           }
       }
   ]
   ```

2. **Grouping and Aggregation**
   ```python
   extra_pipeline = [
       {
           "$group": {
               "_id": "$type",
               "count": {"$sum": 1},
               "avg_age": {"$avg": "$age"}
           }
       }
   ]
   ```

3. **Filtering and Matching**
   ```python
   extra_pipeline = [
       {
           "$match": {
               "age": {"$gt": 30},
               "status": "active"
           }
       }
   ]
   ```

4. **Sorting and Limiting**
   ```python
   extra_pipeline = [
       {
           "$sort": {
               "status": 1,
               "created_at": -1
           }
       },
       {
           "$limit": 5
       }
   ]
   ```

#### Best Practices

1. **Security**
   - Define pipeline stages in the controller to prevent injection
   - Restrict access to sensitive fields
   - Use appropriate indexes for pipeline operations

2. **Performance**
   - Add appropriate indexes for pipeline operations
   - Limit the number of pipeline stages
   - Use efficient aggregation operators

3. **Maintenance**
   - Document the purpose of each pipeline stage
   - Keep pipeline stages simple and focused
   - Test pipeline performance with real data

4. **Error Handling**
   - Handle potential errors in pipeline stages
   - Provide fallback behavior when needed
   - Log pipeline execution for debugging

## Permission System

The RouteController implements a permission-based access control system that requires specific permissions for each CRUD operation. The permissions are automatically generated based on the model name and the action being performed.

### Permission Format

Permissions follow the format `{model_name}:{action}`, where:
- `model_name` is the lowercase name of your model (e.g., "project", "account")
- `action` is one of: "create", "read", "update", "delete"

For example:
- `project:create` - Permission to create new projects
- `project:read` - Permission to view projects
- `project:update` - Permission to modify projects
- `project:delete` - Permission to delete projects

### User Claims

The permission system relies on user claims in the request. The claims should include:
- `permissions`: List of permission strings the user has
- `roles`: List of roles the user has

Example claims:
```json
{
    "account_id": "acc_123",
    "permissions": ["project:create", "project:read"],
    "roles": ["user"]
}
```

### Permission Checks

The system checks permissions in the following order:
1. First checks if the user has the specific permission (e.g., "project:create")
2. If not, checks if the user has an admin or superuser role
3. If neither condition is met, returns a 403 Forbidden error

### Route Permissions

Each route requires specific permissions:

| Route | Method | Permission Required |
|-------|---------|-------------------|
| Create | POST | `{model_name}:create` |
| Get | GET | `{model_name}:read` |
| List | GET | `{model_name}:read` |
| Update | PUT | `{model_name}:update` |
| Delete | DELETE | `{model_name}:delete` |
| List Deleted | GET | `{model_name}:read` |

### Example Usage

```python
from fastapi_sdk.controllers import RouteController
from fastapi_sdk.security.permissions import require_permission

# Create a route controller
route_controller = RouteController(
    prefix="/projects",
    tags=["projects"],
    controller=ProjectController,
    get_db=get_db,
    schema_response=ProjectResponse,
    schema_response_paginated=ProjectResponsePaginated,
    schema_create=ProjectCreate,
    schema_update=ProjectUpdate,
)

# The routes will automatically require the following permissions:
# POST /projects/ -> project:create
# GET /projects/{id} -> project:read
# GET /projects/ -> project:read
# PUT /projects/{id} -> project:update
# DELETE /projects/{id} -> project:delete
# GET /projects/deleted/ -> project:read
```

### Error Responses

When a user lacks the required permission, the API returns a 403 Forbidden response:

```json
{
    "detail": "Permission denied: project:create required"
}
```

### Best Practices

1. **Role-Based Access**: Use roles for broad access control and specific permissions for fine-grained control
2. **Superuser Override**: Superuser roles automatically get access to all operations
3. **Permission Naming**: Keep permission names consistent with your model names
4. **Documentation**: Document required permissions in your API documentation

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
    """Account controller."""

    model = AccountModel
    schema_create = AccountCreate
    schema_update = AccountUpdate
    schema_response = AccountResponse
    cascade_delete = True  # Will delete related projects and tasks
    ownership_rule = OwnershipRule(
        claim_field="account_id",
        model_field="uuid",
        allow_public=False,
    )

    relationships = {
        "projects": {
            "type": "one_to_many",
            "controller": "Project",
            "foreign_key": "account_id",
        }
    }

    # Define custom pipeline stages
    extra_pipeline = [
        {
            "$project": {
                "name": 1,
                "email": 1,
                "status": 1,
                "created_at": 1,
                "is_active": {"$eq": ["$status", "active"]}
            }
        }
    ]

    # The pipeline will be automatically applied to all list queries

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
    schema_response_paginated=AccountResponsePaginated,
    schema_create=AccountCreate,
    schema_update=AccountUpdate,
)

# Include routes
app.include_router(account_routes.router)
``` 