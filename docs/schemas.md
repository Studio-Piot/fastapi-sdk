# Schemas

Schemas are broken down into five components:
- A base schema with always included fields
- A create schema with created_at and updated_ad using datetime_now_sec
- An update schema with updatable data and updated_at
- A response schema for single get requests
- A paginated schema for for multiple items response (list view)

Example:

```python
class AccountBase(BaseModel):
    """Base schema for common attributes"""

    name: str = Field(min_length=2, max_length=50)


class AccountCreate(AccountBase):
    """Schema for creating a account"""

    created_at: datetime = Field(default_factory=datetime_now_sec)
    updated_at: datetime = Field(default_factory=datetime_now_sec)


class AccountUpdate(AccountBase):
    """Schema for updating a account"""

    updated_at: datetime = Field(default_factory=datetime_now_sec)


class AccountResponse(AccountBase):
    """Schema for API responses"""

    uuid: ShortUUIDType
    created_at: datetime
    updated_at: datetime
    deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AccountResponsePaginated(BaseResponsePaginated):
    """Schema for paginatedAPI responses"""

    items: List[AccountResponse]
```