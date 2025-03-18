# ModelController Documentation

The ModelController is a powerful base class for handling CRUD operations with MongoDB using ODMantic and FastAPI. It provides a clean interface for managing models with relationships, pagination, and soft deletion.

## Basic Usage

### 1. Define Your Model

First, create your ODMantic model:

```python
from datetime import datetime
from typing import Optional
from odmantic import Model, Field

class UserModel(Model):
    """User model."""
    created_at: datetime
    updated_at: datetime
    uuid: str = Field(default_factory=lambda: generate_uuid())
    name: str
    email: str
    deleted: bool = False
```

### 2. Define Your Schemas

Create Pydantic schemas for request/response handling:

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    """Schema for creating a user."""
    name: str
    email: str

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user responses."""
    uuid: str
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### 3. Create Your Controller

Create a controller class that inherits from ModelController:

```python
from fastapi_sdk.controllers import ModelController

class User(ModelController):
    """User controller."""
    
    model = UserModel
    schema_create = UserCreate
    schema_update = UserUpdate
    schema_response = UserResponse
    n_per_page = 10  # Optional: customize items per page
```

### 4. Register Your Controller

Register your controller in your FastAPI application:

```python
from fastapi import FastAPI
from fastapi_sdk.controllers import ModelController

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    ModelController.register_controller("User", User)
```

## Available Methods

### Create
```python
user = await User(db_engine).create({"name": "John", "email": "john@example.com"})
```

### Read
```python
# Get single user
user = await User(db_engine).get(uuid="user_123")

# List users with pagination
users = await User(db_engine).list(page=1, order_by={"created_at": -1})
```

### Update
```python
user = await User(db_engine).update(
    uuid="user_123",
    data={"name": "John Updated"}
)
```

### Delete
```python
user = await User(db_engine).delete(uuid="user_123")
```

## Relationships

### Define Relationships

Add relationship definitions to your controller:

```python
class Project(ModelController):
    """Project controller."""
    
    model = ProjectModel
    schema_create = ProjectCreate
    schema_update = ProjectUpdate
    schema_response = ProjectResponse
    
    relationships = {
        "tasks": {
            "type": "one_to_many",
            "controller": "Task",
            "foreign_key": "project_id",
        },
        "owner": {
            "type": "many_to_one",
            "controller": "User",
            "foreign_key": "owner_id",
        }
    }
```

### Fetch Related Data

Use the `include` parameter to fetch related data:

```python
# Get project with its tasks and owner
project = await Project(db_engine).get_with_relations(
    uuid="project_123",
    include=["tasks", "owner"]
)
```

## Cascade Delete

Enable cascade deletion for related models:

```python
class Project(ModelController):
    """Project controller."""
    
    model = ProjectModel
    cascade_delete = True  # Will delete related tasks when project is deleted
```

## Pagination and Filtering

### List with Pagination
```python
# Get first page of users
users = await User(db_engine).list(page=1)

# Get second page with 20 items per page
users = await User(db_engine).list(page=2, n_per_page=20)
```

### Filter Results
```python
# Filter users by email
users = await User(db_engine).list(
    query=[{"email": {"$regex": "@example.com"}}]
)

# Filter with multiple conditions
users = await User(db_engine).list(
    query=[
        {"email": {"$regex": "@example.com"}},
        {"created_at": {"$gte": start_date}}
    ]
)
```

### Sort Results
```python
# Sort by name ascending
users = await User(db_engine).list(order_by={"name": 1})

# Sort by created_at descending
users = await User(db_engine).list(order_by={"created_at": -1})
```

## Response Format

The `list` method returns a paginated response:

```python
{
    "items": [...],  # List of models
    "total": 100,    # Total number of items
    "size": 10,      # Number of items in current page
    "page": 1,       # Current page number
    "pages": 10      # Total number of pages
}
```

## Best Practices

1. Always define your schemas with proper validation
2. Use type hints for better code completion and error checking
3. Register controllers at application startup
4. Use cascade delete carefully as it can have performance implications
5. Consider using indexes for frequently queried fields
6. Use soft deletion (deleted flag) for data integrity
7. Implement proper error handling in your application layer

## Example Implementation

Here's a complete example of a User controller with relationships:

```python
from datetime import datetime
from typing import List, Optional
from odmantic import Model, Field
from pydantic import BaseModel, ConfigDict
from fastapi_sdk.controllers import ModelController

# Model
class UserModel(Model):
    """User model."""
    created_at: datetime
    updated_at: datetime
    uuid: str = Field(default_factory=lambda: generate_uuid())
    name: str
    email: str
    deleted: bool = False

# Schemas
class UserCreate(BaseModel):
    """Schema for creating a user."""
    name: str
    email: str

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user responses."""
    uuid: str
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Controller
class User(ModelController):
    """User controller."""
    
    model = UserModel
    schema_create = UserCreate
    schema_update = UserUpdate
    schema_response = UserResponse
    n_per_page = 10

    relationships = {
        "projects": {
            "type": "one_to_many",
            "controller": "Project",
            "foreign_key": "owner_id",
        }
    }
```

## Ownership Rules

The ModelController supports ownership-based access control through the `OwnershipRule` class. This allows you to restrict access to records based on user claims.

### OwnershipRule Configuration

```python
from fastapi_sdk.controllers import ModelController, OwnershipRule

class ProjectController(ModelController):
    model = ProjectModel
    schema_create = ProjectCreate
    schema_update = ProjectUpdate

    # Configure ownership rule
    ownership_rule = OwnershipRule(
        claim_field="account_id",  # Field in user claims
        model_field="account_id",  # Field in the model
        allow_public=False,  # Whether to allow access without ownership
    )
```

### How Ownership Works

1. **Claim Field**: The field in the user's JWT claims to use for ownership (e.g., "account_id")
2. **Model Field**: The field in your model to match against the claim value
3. **Public Access**: Whether to allow access to records without ownership

### Ownership in CRUD Operations

The ownership rule affects all CRUD operations:

- **Create**: Verifies that the provided data matches the user's claim
- **Read**: Only returns records owned by the user
- **Update**: Only allows updating owned records
- **Delete**: Only allows deleting owned records
- **List**: Only returns records owned by the user

### Example Usage

```python
# User claims from JWT
claims = {
    "account_id": "acc_123",
    "roles": ["user"]
}

# Create a project
project = await controller.create(
    data={"name": "My Project", "account_id": "acc_123"},
    claims=claims
)  # Success

# Try to create a project for another account
project = await controller.create(
    data={"name": "My Project", "account_id": "acc_456"},
    claims=claims
)  # 403 Forbidden

# List projects
projects = await controller.list(claims=claims)
# Only returns projects where account_id = "acc_123"

# Get a project
project = await controller.get("project_123", claims=claims)
# Only succeeds if project.account_id = "acc_123"
```

### Error Handling

The ownership system will return appropriate errors:

- **Missing Claim**: 403 Forbidden if required claim is missing
- **Invalid Ownership**: 403 Forbidden if trying to access/modify records owned by another user
- **Not Found**: 404 Not Found if record doesn't exist or user doesn't have access

### Public Access

You can allow public access to records by setting `allow_public=True`:

```python
class PublicProjectController(ModelController):
    ownership_rule = OwnershipRule(
        claim_field="account_id",
        model_field="account_id",
        allow_public=True  # Anyone can access these records
    )
```

### Best Practices

1. **Consistent Field Names**: Use consistent field names between claims and models
2. **Public Access**: Only enable public access when necessary
3. **Error Messages**: Provide clear error messages for ownership violations
4. **Testing**: Test both owned and non-owned access scenarios 