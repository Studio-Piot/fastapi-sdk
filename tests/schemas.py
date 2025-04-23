"""Schemas for API requests and responses.

This module defines Pydantic models for validating and serializing data in the API.
It includes schemas for:
- Accounts: Creating, updating, and returning account data
- Projects: Managing project information
- Tasks: Handling task-related data

Each model type has Base, Create, Update, and Response schemas to handle different
API operations appropriately.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from fastapi_sdk.utils.model import ShortUUIDType
from fastapi_sdk.utils.schema import BaseResponsePaginated, datetime_now_sec
from tests.constants import TaskStatusOptions

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
    projects: Optional[List["ProjectResponse"]] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)


class AccountResponsePaginated(BaseResponsePaginated):
    """Schema for paginatedAPI responses"""

    items: List[AccountResponse]


###########
# Project #
###########


class ProjectBase(BaseModel):
    """Base schema for common attributes"""

    name: str = Field(min_length=2, max_length=50)
    account_id: str


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""

    created_at: datetime = Field(default_factory=datetime_now_sec)
    updated_at: datetime = Field(default_factory=datetime_now_sec)


class ProjectUpdate(ProjectBase):
    """Schema for updating a project"""

    account_id: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime_now_sec)


class ProjectResponse(ProjectBase):
    """Schema for API responses"""

    uuid: ShortUUIDType
    created_at: datetime
    updated_at: datetime
    deleted: bool
    tasks: Optional[List["TaskResponse"]] = Field(default=None)
    latest_task: Optional["TaskResponse"] = Field(default=None)
    account: Optional["AccountResponse"] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)


class ProjectResponsePaginated(BaseResponsePaginated):
    """Schema for paginated API responses"""

    items: List[ProjectResponse]


###########
# Task #
###########


class TaskBase(BaseModel):
    """Base schema for common attributes"""

    name: str = Field(min_length=2, max_length=50)
    description: Optional[str] = Field(min_length=0, max_length=1000, default=None)
    project_id: str
    account_id: str
    assignee_ids: Optional[List[str]] = Field(default=None)
    due_date: Optional[datetime] = Field(default=None)
    status: Optional[TaskStatusOptions] = TaskStatusOptions.TO_DO


class TaskCreate(TaskBase):
    """Schema for creating a task"""

    created_at: datetime = Field(default_factory=datetime_now_sec)
    updated_at: datetime = Field(default_factory=datetime_now_sec)


class TaskUpdate(TaskBase):
    """Schema for updating a task"""

    name: Optional[str] = Field(min_length=2, max_length=50, default=None)
    project_id: Optional[str] = Field(default=None)
    account_id: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime_now_sec)


class TaskResponse(TaskBase):
    """Schema for API responses"""

    uuid: ShortUUIDType
    created_at: datetime
    updated_at: datetime
    deleted: bool
    project: Optional["ProjectResponse"] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class TaskResponsePaginated(BaseResponsePaginated):
    """Schema for paginated API responses"""

    items: List[TaskResponse]
