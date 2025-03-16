from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from fastapi_sdk.utils.model import ShortUUIDType
from fastapi_sdk.utils.schema import datetime_now_sec

###########
# Account #
###########


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
