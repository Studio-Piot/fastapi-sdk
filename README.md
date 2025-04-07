# FastAPI SDK

A powerful SDK for building FastAPI applications with built-in authentication, authorization, and CRUD operations.

## Features

- 🔐 **Authentication & Authorization**
  - JWT-based authentication
  - Role-based access control
  - Fine-grained permissions
  - User claims management

- 🗄️ **Database Operations**
  - Automatic CRUD operations
  - Soft delete support
  - Pagination
  - Relationship handling

- 🛡️ **Security**
  - Ownership-based access control
  - Permission-based authorization
  - Role-based access control
  - Secure token handling

- 📝 **Type Safety**
  - Pydantic model integration
  - Type hints throughout
  - Automatic validation
  - OpenAPI documentation

## Documentation

- [Route Controller Documentation](docs/route_controller.md) - Learn how to create CRUD routes with authentication and permissions
- [Model Controller Documentation](docs/model_controller.md) - Understand how to implement database operations and relationships


## Quick Start

Using UV, start a new project from within the folder you wish to create it.

> The project requires Python 3.13 or above.

```bash
uv init
uv venv
source .venv/bin/activaye
uv add fastapi-sdk
```

In order to test authentication, we need a set of asymmetric encryption keys for test access tokens. Generate the two keys using the command below:

```
openssl genrsa -des3 -out test_private_encrypted.pem 2048
openssl rsa -pubout -in test_private_encrypted.pem -out test_public_key.pem
openssl rsa -in test_private_encrypted.pem -out test_private_key.pem -outform PEM
```

This will create three keys:

- `test_private_encrypted.pem` (keep safe somewhere)
- `test_private_key.pem`
- `test_public_key.pem`

We will use the `test_private_key.pem` key to encrypt our JWT tokens and `test_public_key.pem` to decrypt them (asymmetric encryption).

> Those test keys can added to the repository for ease of setup and running CI/CD testing.

Add the value of each key to your environment:

```bash
# .env.local
export TEST_PRIVATE_KEY_PATH="test_private_key.pem"
export TEST_PUBLIC_KEY_PATH="test_public_key.pem"
```

For the API to work in the real world, you will need settings for Fauthy authentication. Create a new tenant and use the `client_id` which will be required to get the public JWKs.

```bash
# .env.local
export AUTH_ISSUER="https://identity.piot.co.uk"
export AUTH_CLIENT_ID="test_client_id" # Replace with real client_id for production
```

Then some api settings:

```bash
# .env.local
export PUBLIC_ROUTES="/public/*,/other"
export ENVIRONMENT="development" # Replace with production when deploying to live server
```

A full `.env.local` complete included the MongoDB connection string:

```bash
export AUTH_PRIVATE_KEY="test_private_key.pem"
export AUTH_PUBLIC_KEY="test_public_key.pem"
export AUTH_ISSUER="https://identity.piot.co.uk"
export AUTH_CLIENT_ID="test_client_id" # Replace with real client_id for production
export PUBLIC_ROUTES="/public/*,/other"
export ENVIRONMENT="development" # Replace with production when deploying to live server
export MONGO_DATABASE_URI="mongodb://localhost:27017"
export MONGO_DATABASE_NAME="fastapi_sdk_test"
```

```python
from fastapi import FastAPI
from fastapi_sdk.controllers.route import RouteController
from fastapi_sdk.middleware.auth import AuthMiddleware
from fastapi_sdk.controllers import ModelController
from fastapi_sdk.controllers.model import OwnershipRule
from tests.models import AccountModel
from tests.schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
)


class Account(ModelController):
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

app = FastAPI()

# Add authentication middleware
app.add_middleware(
    AuthMiddleware,
    public_routes=["/docs", "/openapi.json"],  # Routes that don't require authentication
    auth_issuer="https://your-auth-server.com",  # The issuer of the JWT tokens
    auth_client_id="your-client-id",  # Your application's client ID
    env="prod",  # Environment: "test" or "prod"
    # Optional: Test environment keys
    test_private_key_path="path/to/private.key",  # Only needed for test environment
    test_public_key_path="path/to/public.key",  # Only needed for test environment
)

# Create a route controller
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

## Development

### Setup

1. Clone the repository
2. Install dependencies:
```bash
uv sync
```

### Running Tests

```bash
pytest
```

## License

MIT License - see LICENSE file for details
