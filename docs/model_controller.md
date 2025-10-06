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

# Get user with related projects included
user = await User(db_engine).get(
    uuid="user_123",
    include=["projects"]
)

# Get user with multiple relations included
user = await User(db_engine).get(
    uuid="user_123",
    include=["projects", "tasks"]
)

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

### Undelete
```python
user = await User(db_engine).undelete(uuid="user_123")
```

### Get with Relations
```python
# Get user with related projects
user = await User(db_engine).get_with_relations(
    uuid="user_123",
    include=["projects"]
)

# Get with include parameter (alternative to get_with_relations)
user = await User(db_engine).get(
    uuid="user_123",
    include=["projects"]
)
```

### Delete with Relations
```python
# Delete user and related projects
result = await User(db_engine).delete_with_relations(
    uuid="user_123"
)
```

### List Related
```python
# List all projects for a user
projects = await Project(db_engine).list_related(
    foreign_key="user_id",
    value="user_123"
)
```

### List with Relations
```python
# List users with their projects included
users = await User(db_engine).list(
    include=["projects"]  # Include related projects
)

# List users with multiple relations included
users = await User(db_engine).list(
    include=["projects", "tasks"]  # Include both projects and tasks
)

# List with pagination and relations
users = await User(db_engine).list(
    page=1,
    order_by={"created_at": -1},
    include=["projects"]
)
```

### Get with Relations
```python
# Get user with their projects included
user = await User(db_engine).get_with_relations(
    uuid="user_123",
    include=["projects"]  # Include related projects
)

# Get user with multiple relations included
user = await User(db_engine).get_with_relations(
    uuid="user_123",
    include=["projects", "tasks"]  # Include both projects and tasks
)

# Alternative: Use get method with include parameter
user = await User(db_engine).get(
    uuid="user_123",
    include=["projects", "tasks"]  # Include both projects and tasks
)
```

### Get Single Object with Relations

The `get` method now supports the `include` parameter to load related objects:

```python
# Get a user with their projects included
user = await User(db_engine).get(
    uuid="user_123",
    include=["projects"]
)

# Get a project with its account and tasks
project = await Project(db_engine).get(
    uuid="project_123",
    include=["account", "tasks"]
)

# Get a task with its project
task = await Task(db_engine).get(
    uuid="task_123",
    include=["project"]
)
```

**Benefits of using `get` with `include`:**
- More efficient than `get_with_relations` for single objects
- Consistent interface with the `list` method
- Supports both one-to-many and many-to-one relationships
- Gracefully handles non-existent relationships

### Response Format with Relations

When using the `include` parameter, the response will include the related objects as nested fields:

```python
# Example response for list with projects included
{
    "items": [
        {
            "uuid": "user_123",
            "name": "John",
            "email": "john@example.com",
            "projects": [  # Included projects
                {
                    "uuid": "project_1",
                    "name": "Project 1",
                    "owner_id": "user_123"
                },
                {
                    "uuid": "project_2",
                    "name": "Project 2",
                    "owner_id": "user_123"
                }
            ]
        }
    ],
    "total": 1,
    "page": 0,
    "pages": 1,
    "size": 1
}

# Example response for get with projects included
{
    "uuid": "user_123",
    "name": "John",
    "email": "john@example.com",
    "projects": [  # Included projects
        {
            "uuid": "project_1",
            "name": "Project 1",
            "owner_id": "user_123"
        },
        {
            "uuid": "project_2",
            "name": "Project 2",
            "owner_id": "user_123"
        }
    ]
}

# Example response for get with many-to-one relationship
{
    "uuid": "project_1",
    "name": "Project 1",
    "owner_id": "user_123",
    "account": {  # Included account (many-to-one)
        "uuid": "acc_123",
        "name": "Test Account",
        "email": "account@example.com"
    }
}
```

### Best Practices for Using Relations

1. **Performance Considerations**
   - Be mindful of the number of relations you include
   - Consider using pagination for large related collections
   - Use indexes on foreign key fields for better performance

2. **Error Handling**
   - Non-existent relations are silently ignored
   - Invalid relation names are skipped
   - The response will still include the main object even if relation loading fails

3. **Ownership and Permissions**
   - Relations are filtered based on the same ownership rules as the main object
   - Users can only access related objects they have permission to view

4. **Caching**
   - Consider implementing caching for frequently accessed relations
   - Use appropriate cache invalidation strategies when related objects change

5. **Documentation**
   - Document available relations in your API documentation
   - Provide examples of common include patterns
   - Explain any performance implications of including specific relations

## Hooks

The ModelController provides hooks that can be overridden to add custom behavior before and after create and update operations.

### Before Create Hook

The `before_create` hook is called before a model is created and saved to the database. This is useful for:
- Adding computed fields
- Setting default values
- Adding user-specific data from claims
- Performing pre-creation validations
- Modifying input data

Example:
```python
class UserController(ModelController):
    model = UserModel
    schema_create = UserCreate
    schema_update = UserUpdate

    async def before_create(self, data_dict: dict, claims: Optional[Dict[str, Any]] = None) -> dict:
        """Before create hook to add user-specific data."""
        if claims and "user_id" in claims:
            data_dict["created_by"] = claims["user_id"]
        return data_dict
```

### Before Update Hook

The `before_update` hook is called before a model is updated and saved to the database. This is useful for:
- Adding audit fields
- Setting modification timestamps
- Adding user-specific data from claims
- Performing pre-update validations
- Modifying update data

Example:
```python
class UserController(ModelController):
    model = UserModel
    schema_create = UserCreate
    schema_update = UserUpdate

    async def before_update(self, data_dict: dict, claims: Optional[Dict[str, Any]] = None) -> dict:
        """Before update hook to add audit fields."""
        if claims and "user_id" in claims:
            data_dict["updated_by"] = claims["user_id"]
        return data_dict
```

### After Create Hook

The `after_create` hook is called after a model is created and saved to the database. This is useful for:
- Computing derived fields
- Setting up related data
- Triggering notifications
- Performing post-creation validations

Example:
```python
class RoleController(ModelController):
    model = RoleModel
    schema_create = RoleCreate
    schema_update = RoleUpdate

    async def after_create(self, obj: RoleModel, claims: Optional[dict] = None) -> RoleModel:
        """After create hook to compute permission names."""
        obj.permission_names = [
            await self.db_engine.find_one(
                PermissionModel, PermissionModel.uuid == permission
            ).name
            for permission in obj.permissions
        ]
        return obj
```

### After Update Hook

The `after_update` hook is called after a model is updated and saved to the database. This is useful for:
- Updating derived fields
- Maintaining data consistency
- Triggering notifications
- Performing post-update validations

Example:
```python
class RoleController(ModelController):
    model = RoleModel
    schema_create = RoleCreate
    schema_update = RoleUpdate

    async def after_update(self, obj: RoleModel, claims: Optional[dict] = None) -> RoleModel:
        """After update hook to recompute permission names."""
        obj.permission_names = [
            await self.db_engine.find_one(
                PermissionModel, PermissionModel.uuid == permission
            ).name
            for permission in obj.permissions
        ]
        return obj
```

### Hook Best Practices

1. **Return the Object**: Always return the modified object from the hook
2. **Async Operations**: Use async/await for database operations in hooks
3. **Error Handling**: Handle potential errors in hooks gracefully
4. **Performance**: Keep hooks lightweight to avoid impacting response times
5. **Idempotency**: Design hooks to be idempotent when possible
6. **Documentation**: Document the purpose and behavior of hooks
7. **Claims Handling**: Always check if claims exist before accessing them
8. **Data Modification**: Be careful when modifying input data in before hooks
9. **Validation**: Use before hooks for input validation when needed
10. **Side Effects**: Use after hooks for side effects like notifications

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

### Customizing Items Per Page

You can customize the number of items per page in two ways:

1. **Class-level Default**
   ```python
   class User(ModelController):
       """User controller."""
       n_per_page = 25  # Set default items per page to 25
   ```

2. **Per-Request Customization**
   ```python
   # Get first page with 50 items
   users = await User(db_engine).list(page=0, n_per_page=50)
   ```

The `n_per_page` parameter has a maximum limit of 250 items per page. If a larger value is provided, it will be automatically capped at 250.

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
    "page": 1,       # Current page number (1-based)
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

### Array-Based Ownership

The ownership system supports both single values and arrays in the claim field:

- **Single Value**: When the claim contains a single value, the system filters records where the model field matches that exact value
- **Array of Values**: When the claim contains an array of values, the system filters records where the model field matches any value in the array

This allows users to have access to records from multiple accounts, organizations, or other entities.

### Ownership in CRUD Operations

The ownership rule affects all CRUD operations:

- **Create**: Verifies that the provided data matches the user's claim
- **Read**: Only returns records owned by the user
- **Update**: Only allows updating owned records
- **Delete**: Only allows deleting owned records
- **List**: Only returns records owned by the user

### Example Usage

#### Single Value Ownership

```python
# User claims from JWT with single account
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

#### Array-Based Ownership

```python
# User claims from JWT with multiple accounts
claims = {
    "account_id": ["acc_123", "acc_456", "acc_789"],
    "roles": ["admin"]
}

# Create a project for any of the user's accounts
project = await controller.create(
    data={"name": "My Project", "account_id": "acc_123"},
    claims=claims
)  # Success

# Create a project for another account the user has access to
project = await controller.create(
    data={"name": "Another Project", "account_id": "acc_456"},
    claims=claims
)  # Success

# Try to create a project for an account the user doesn't have access to
project = await controller.create(
    data={"name": "Unauthorized Project", "account_id": "acc_999"},
    claims=claims
)  # 403 Forbidden

# List projects
projects = await controller.list(claims=claims)
# Returns projects where account_id is in ["acc_123", "acc_456", "acc_789"]

# Get a project
project = await controller.get("project_123", claims=claims)
# Succeeds if project.account_id is in ["acc_123", "acc_456", "acc_789"]

# Update a project
updated_project = await controller.update(
    "project_123", 
    {"name": "Updated Project"}, 
    claims=claims
)
# Succeeds if project.account_id is in the user's account list

# Delete a project
deleted_project = await controller.delete("project_123", claims=claims)
# Succeeds if project.account_id is in the user's account list
```

#### Empty Array Handling

```python
# User claims with empty account list
claims = {
    "account_id": [],
    "roles": ["user"]
}

# All operations will fail with 403 Forbidden
# because the user has no accounts they can access
```

#### Ownership with User Queries

The ownership system intelligently handles conflicts between ownership filters and user-provided queries:

```python
# User has access to multiple accounts
claims = {
    "account_id": ["acc_123", "acc_456", "acc_789"],
    "roles": ["admin"]
}

# List all projects (returns projects for all three accounts)
projects = await controller.list(claims=claims)

# Filter for specific account (allowed if user has access)
projects = await controller.list(
    query=[{"account_id": "acc_123"}], 
    claims=claims
)  # Success - returns only projects for acc_123

# Try to filter for account user doesn't have access to
projects = await controller.list(
    query=[{"account_id": "acc_999"}], 
    claims=claims
)  # 403 Forbidden - user doesn't have access to acc_999

# Filter with array query that intersects with ownership
projects = await controller.list(
    query=[{"account_id": {"$in": ["acc_123", "acc_999"]}}], 
    claims=claims
)  # Success - returns only projects for acc_123 (intersection)

# Filter with array query that has no intersection
projects = await controller.list(
    query=[{"account_id": {"$in": ["acc_999", "acc_888"]}}], 
    claims=claims
)  # 403 Forbidden - no intersection with user's allowed accounts
```

**How it works:**
- If user query doesn't specify the ownership field, the ownership filter is applied normally
- If user query specifies the same field as ownership, the system finds the intersection
- Single value queries are checked against the ownership list
- Array queries are intersected with the ownership list
- If there's no intersection, access is denied with a 403 error

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
5. **Array Ownership**: When using array-based ownership:
   - Ensure the claim field contains valid values
   - Handle empty arrays appropriately (they will deny all access)
   - Consider performance implications of large arrays
   - Use consistent data types in the array (all strings, all integers, etc.)
   - Be aware that user queries on the same field will be intersected with ownership
   - Design your API to handle 403 errors when users query for unauthorized values
6. **Security**: 
   - Validate claim values on the server side
   - Implement proper JWT token validation
   - Consider rate limiting for operations with large claim arrays
7. **Performance**:
   - Use database indexes on ownership fields
   - Consider caching for frequently accessed ownership data
   - Monitor query performance with large claim arrays

## Complete API Reference

### Core Methods

#### `create(data: dict, claims: Optional[Dict[str, Any]] = None) -> BaseModel`
Creates a new model instance with the provided data.

**Parameters:**
- `data`: Dictionary containing model attributes
- `claims`: Optional user claims for ownership verification

**Returns:**
- The created model instance

#### `count(query: Optional[List[dict]] = None, claims: Optional[Dict[str, Any]] = None, deleted: bool = False) -> int`
Counts the number of models matching the query criteria.

**Parameters:**
- `query`: Optional list of query dictionaries for filtering
- `claims`: Optional user claims for ownership verification
- `deleted`: If True, only count deleted items. If False, only count non-deleted items

**Returns:**
- Integer representing the total count of matching items

**Example:**
```python
# Count all non-deleted items
total = await controller.count()

# Count deleted items
deleted_count = await controller.count(deleted=True)

# Count with query
active_count = await controller.count(
    query=[{"status": "active"}],
    claims={"account_id": "acc_123"}
)
```

#### `get(uuid: str, claims: Optional[Dict[str, Any]] = None, include_deleted: bool = False, include: Optional[List[str]] = None) -> Optional[BaseModel]`
Retrieves a single model by UUID.

**Parameters:**
- `uuid`: The UUID of the model to retrieve
- `claims`: Optional user claims for ownership verification
- `include_deleted`: Whether to include deleted models
- `include`: Optional list of relationship names to include

**Returns:**
- The model instance or None if not found

**Example:**
```python
# Get a user without relations
user = await controller.get(uuid="user_123")

# Get a user with projects included
user = await controller.get(
    uuid="user_123",
    include=["projects"]
)

# Get a user with multiple relations
user = await controller.get(
    uuid="user_123",
    include=["projects", "tasks", "account"]
)
```

#### `update(uuid: str, data: dict, claims: Optional[Dict[str, Any]] = None) -> Optional[BaseModel]`
Updates an existing model.

**Parameters:**
- `uuid`: The UUID of the model to update
- `data`: Dictionary containing fields to update
- `claims`: Optional user claims for ownership verification

**Returns:**
- The updated model instance or None if not found

#### `delete(uuid: str, claims: Optional[Dict[str, Any]] = None) -> Optional[BaseModel]`
Soft deletes a model by setting the `deleted` flag to True.

**Parameters:**
- `uuid`: The UUID of the model to delete
- `claims`: Optional user claims for ownership verification

**Returns:**
- The deleted model instance or None if not found

#### `undelete(uuid: str, claims: Optional[Dict[str, Any]] = None) -> Optional[BaseModel]`
Undeletes a model by setting the `deleted` flag to False.

**Parameters:**
- `uuid`: The UUID of the model to undelete
- `claims`: Optional user claims for ownership verification

**Returns:**
- The undeleted model instance or None if not found

#### `list(page: int = 1, query: Optional[List[dict]] = None, order_by: Optional[dict] = None, claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
Lists models with pagination and filtering.

**Parameters:**
- `page`: Page number (1-based, minimum 1)
- `query`: List of query dictionaries for filtering
- `order_by`: Dictionary for sorting (e.g., `{"created_at": -1}`)
- `claims`: Optional user claims for ownership verification

**Returns:**
- Dictionary containing items, total count, page info, etc.

### Relationship Methods

#### `get_with_relations(uuid: str, include: Optional[List[str]] = None, claims: Optional[Dict[str, Any]] = None) -> BaseModel`
Retrieves a model with its related models.

**Parameters:**
- `uuid`: The UUID of the model to retrieve
- `include`: List of relationship names to include
- `claims`: Optional user claims for ownership verification

**Returns:**
- The model with related models attached as attributes

#### `delete_with_relations(uuid: str, claims: Optional[Dict[str, Any]] = None) -> BaseModel`
Deletes a model and its related models if cascade_delete is enabled.

**Parameters:**
- `uuid`: The UUID of the model to delete
- `claims`: Optional user claims for ownership verification

**Returns:**
- The deleted model instance

#### `list_related(foreign_key: str, value: str, claims: Optional[Dict[str, Any]] = None) -> List[BaseModel]`
Lists models related to another model by foreign key.

**Parameters:**
- `foreign_key`: The foreign key field name
- `value`: The value to match against
- `claims`: Optional user claims for ownership verification

**Returns:**
- List of related model instances

### Hook Methods

#### `after_create(obj: BaseModel, claims: Optional[dict] = None) -> BaseModel`
Hook called after creating a model.

**Parameters:**
- `obj`: The created model instance
- `claims`: Optional user claims for ownership verification

**Returns:**
- The modified model instance

#### `after_update(obj: BaseModel, claims: Optional[dict] = None) -> BaseModel`
Hook called after updating a model.

**Parameters:**
- `obj`: The updated model instance
- `claims`: Optional user claims for ownership verification

**Returns:**
- The modified model instance

### Utility Methods

#### `_get_ownership_filter(claims: Dict[str, Any]) -> Optional[Dict[str, Any]]`
Gets the ownership filter based on user claims.

**Parameters:**
- `claims`: User claims from JWT token

**Returns:**
- Filter dictionary or None if no ownership rule is set

#### `register_controller(name: str, controller_class: Type["ModelController"]) -> None`
Registers a controller class in the controller registry.

**Parameters:**
- `name`: Name to register the controller under
- `controller_class`: The controller class to register

#### `get_controller(name: str) -> Type["ModelController"]`
Gets a controller class from the registry.

**Parameters:**
- `name`: Name of the controller to retrieve

**Returns:**
- The controller class

### Best Practices for Using Relations

1. **Performance Considerations**
   - Be mindful of the number of relations you include
   - Consider using pagination for large related collections
   - Use indexes on foreign key fields for better performance

2. **Error Handling**
   - Non-existent relations are silently ignored
   - Invalid relation names are skipped
   - The response will still include the main object even if relation loading fails

3. **Ownership and Permissions**
   - Relations are filtered based on the same ownership rules as the main object
   - Users can only access related objects they have permission to view

4. **Caching**
   - Consider implementing caching for frequently accessed relations
   - Use appropriate cache invalidation strategies when related objects change

5. **Documentation**
   - Document available relations in your API documentation
   - Provide examples of common include patterns
   - Explain any performance implications of including specific relations

## Advanced Features

### Custom Aggregation Pipeline

The ModelController supports custom MongoDB aggregation pipeline stages through the `extra_pipeline` class attribute. This allows you to add complex aggregation operations to your queries.

#### Using extra_pipeline

```python
class UserController(ModelController):
    model = UserModel
    schema_create = UserCreate
    schema_update = UserUpdate

    # Define custom pipeline stages
    extra_pipeline = [
        # Example: Add a computed field
        {
            "$addFields": {
                "full_name": {
                    "$concat": ["$first_name", " ", "$last_name"]
                }
            }
        },
        # Example: Group and calculate statistics
        {
            "$group": {
                "_id": "$department",
                "avg_age": {"$avg": "$age"},
                "count": {"$sum": 1}
            }
        }
    ]
```

#### Pipeline Stage Order

The custom pipeline stages are added after the basic query and before pagination. The order of operations is:

1. Basic query filtering (including ownership rules)
2. Custom pipeline stages (extra_pipeline)
3. Sorting
4. Pagination

#### Common Use Cases

1. **Computed Fields**
```python
extra_pipeline = [
    {
        "$addFields": {
            "age": {
                "$subtract": [
                    {"$year": "$$NOW"},
                    {"$year": "$birth_date"}
                ]
            }
        }
    }
]
```

2. **Data Transformation**
```python
extra_pipeline = [
    {
        "$project": {
            "name": 1,
            "email": 1,
            "formatted_created_at": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": "$created_at"
                }
            }
        }
    }
]
```

3. **Aggregation**
```python
extra_pipeline = [
    {
        "$group": {
            "_id": "$category",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }
    }
]
```

#### Best Practices

1. **Performance**
   - Keep pipeline stages efficient
   - Use indexes that support your pipeline operations
   - Avoid unnecessary transformations

2. **Maintainability**
   - Document complex pipeline stages
   - Break down complex operations into multiple stages
   - Use meaningful field names

3. **Compatibility**
   - Ensure pipeline stages work with pagination
   - Consider the impact on response format
   - Test with different query parameters

4. **Error Handling**
   - Handle missing fields gracefully
   - Use `$ifNull` for default values
   - Consider edge cases in aggregations

#### Example Implementation

Here's a complete example of a controller using custom pipeline stages:

```python
class SalesController(ModelController):
    model = SalesModel
    schema_create = SalesCreate
    schema_update = SalesUpdate

    extra_pipeline = [
        # Add computed fields
        {
            "$addFields": {
                "profit": {
                    "$subtract": ["$revenue", "$cost"]
                },
                "profit_margin": {
                    "$multiply": [
                        {
                            "$divide": [
                                {"$subtract": ["$revenue", "$cost"]},
                                "$revenue"
                            ]
                        },
                        100
                    ]
                }
            }
        },
        # Add status based on profit margin
        {
            "$addFields": {
                "status": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$gte": ["$profit_margin", 20]},
                                "then": "excellent"
                            },
                            {
                                "case": {"$gte": ["$profit_margin", 10]},
                                "then": "good"
                            }
                        ],
                        "default": "needs_attention"
                    }
                }
            }
        }
    ]
```

This will automatically apply these transformations to all list queries, adding computed fields for profit, profit margin, and status based on the profit margin.

## Best Practices

1. Always define your schemas with proper validation
2. Use type hints for better code completion and error checking
3. Register controllers at application startup
4. Use cascade delete carefully as it can have performance implications
5. Consider using indexes for frequently queried fields
6. Use soft deletion (deleted flag) for data integrity
7. Implement proper error handling in your application layer
8. Document complex pipeline stages when using extra_pipeline
9. Test aggregation pipelines with different data scenarios
10. Monitor performance of custom pipeline stages 