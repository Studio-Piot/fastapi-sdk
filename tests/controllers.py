"""Controllers for tests."""

from typing import List, Optional

from fastapi_sdk.controllers import ModelController
from tests.models import AccountModel, ProjectModel, TaskModel
from tests.schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)


class Account(ModelController):
    """Account controller."""

    model = AccountModel
    schema_create = AccountCreate
    schema_update = AccountUpdate
    schema_response = AccountResponse
    cascade_delete = True  # Will delete related projects and tasks

    relationships = {
        "projects": {
            "type": "one_to_many",
            "controller": "Project",
            "foreign_key": "account_id",
        }
    }


class Project(ModelController):
    """Project controller."""

    model = ProjectModel
    schema_create = ProjectCreate
    schema_update = ProjectUpdate
    schema_response = ProjectResponse
    cascade_delete = True  # Will delete related tasks

    relationships = {
        "account": {
            "type": "many_to_one",
            "controller": "Account",
            "foreign_key": "account_id",
        },
        "tasks": {
            "type": "one_to_many",
            "controller": "Task",
            "foreign_key": "project_id",
        },
    }


class Task(ModelController):
    """Task controller."""

    model = TaskModel
    schema_create = TaskCreate
    schema_update = TaskUpdate
    schema_response = TaskResponse

    relationships = {
        "account": {
            "type": "many_to_one",
            "controller": "Account",
            "foreign_key": "account_id",
        },
        "project": {
            "type": "many_to_one",
            "controller": "Project",
            "foreign_key": "project_id",
        },
    }
