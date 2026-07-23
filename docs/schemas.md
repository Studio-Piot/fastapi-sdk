# Schemas

Schemas are Pydantic classes used for **request and response data** on routes. They validate incoming payloads and shape outgoing API responses.

They are distinct from **database models** (ODMantic `Model` classes), which define how data is stored. See [Model Controller](model_controller.md) for database models.

## Schema types

Schemas are typically broken down into five components:

| Schema | Purpose |
|--------|---------|
| **Base** | Shared fields used by create/update/response |
| **Create** | Body for `POST` (often includes `created_at` / `updated_at`) |
| **Update** | Body for `PUT`/`PATCH` (updatable fields + `updated_at`) |
| **Response** | Single-item response (e.g. `GET /{uuid}`) |
| **Paginated** | List response wrapper (`items`, pagination meta) |

These are passed into `RouteController` / `ModelController` as `schema_create`, `schema_update`, `schema_response`, and `schema_response_paginated`. See [Route Controller](route_controller.md) for wiring them to routes.

## Example

```python
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from fastapi_sdk.utils.model import ShortUUIDType
from fastapi_sdk.utils.schema import BaseResponsePaginated, datetime_now_sec


class AccountBase(BaseModel):
    """Base schema for common attributes."""

    name: str = Field(min_length=2, max_length=50)


class AccountCreate(AccountBase):
    """Schema for creating an account."""

    created_at: datetime = Field(default_factory=datetime_now_sec)
    updated_at: datetime = Field(default_factory=datetime_now_sec)


class AccountUpdate(AccountBase):
    """Schema for updating an account."""

    updated_at: datetime = Field(default_factory=datetime_now_sec)


class AccountResponse(AccountBase):
    """Schema for API responses."""

    uuid: ShortUUIDType
    created_at: datetime
    updated_at: datetime
    deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AccountResponsePaginated(BaseResponsePaginated):
    """Schema for paginated API responses."""

    items: List[AccountResponse]
```
