"""Database represenation of an object."""

from datetime import datetime
from typing import List, Optional

from odmantic import EmbeddedModel, Field, Index, Model

from fastapi_sdk.utils.model import ShortUUID, ShortUUIDType
from tests.constants import TaskStatusOptions


class AccountModel(Model):
    """Account model"""

    created_at: datetime
    updated_at: datetime
    uuid: ShortUUIDType = Field(default_factory=lambda: ShortUUID.generate("acc"))
    name: Optional[str] = Field(default=None)
    deleted: bool = False
    projects: Optional[List["ProjectModel"]] = Field(default=None)

    model_config = {
        "indexes": lambda: [
            Index(AccountModel.uuid, unique=True),
        ]
    }


class ProjectModel(Model):
    """Project model"""

    created_at: datetime
    updated_at: datetime
    uuid: ShortUUIDType = Field(default_factory=lambda: ShortUUID.generate("prj"))
    account_id: str
    name: Optional[str] = Field(default=None)
    deleted: bool = False
    account: Optional["AccountModel"] = Field(default=None)
    tasks: Optional[List["TaskModel"]] = Field(default=None)

    model_config = {
        "indexes": lambda: [
            Index(ProjectModel.uuid, unique=True),
        ]
    }


class TaskModel(Model):
    """Task model"""

    created_at: datetime
    updated_at: datetime
    uuid: ShortUUIDType = Field(default_factory=lambda: ShortUUID.generate("tsk"))
    account_id: str
    project_id: str
    assignee_ids: Optional[List[str]] = Field(default=None)
    name: str
    description: Optional[str] = Field(default=None)
    status: Optional[TaskStatusOptions] = TaskStatusOptions.TO_DO
    due_date: Optional[datetime] = Field(default=None)
    deleted: bool = False
    account: Optional["AccountModel"] = Field(default=None)
    project: Optional["ProjectModel"] = Field(default=None)

    model_config = {
        "indexes": lambda: [
            Index(TaskModel.uuid, unique=True),
        ]
    }
