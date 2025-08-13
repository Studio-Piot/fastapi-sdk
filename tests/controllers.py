"""Controllers for tests."""

from fastapi_sdk.controllers import ModelController
from fastapi_sdk.controllers.model import OwnershipRule
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


class Project(ModelController):
    """Project controller."""

    model = ProjectModel
    schema_create = ProjectCreate
    schema_update = ProjectUpdate
    schema_response = ProjectResponse
    cascade_delete = True  # Will delete related tasks
    ownership_rule = OwnershipRule(
        claim_field="account_id",
        model_field="account_id",
        allow_public=False,
    )

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

    # Custom pipeline to get the last task by name
    extra_pipeline = [
        {
            "$lookup": {
                "from": "task",
                "localField": "uuid",
                "foreignField": "project_id",
                "as": "tasks_for_project",
            }
        },
        {
            "$addFields": {
                "latest_task": {
                    "$arrayElemAt": [
                        {
                            "$sortArray": {
                                "input": "$tasks_for_project",
                                "sortBy": {"name": -1},
                            }
                        },
                        0,
                    ]
                }
            }
        },
        {
            "$project": {
                "tasks_for_project": 0  # Remove the tasks array since we only need latest_task
            }
        },
    ]


class Task(ModelController):
    """Task controller."""

    model = TaskModel
    schema_create = TaskCreate
    schema_update = TaskUpdate
    schema_response = TaskResponse
    ownership_rule = OwnershipRule(
        claim_field="account_id",
        model_field="account_id",
        allow_public=False,
    )

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


class PublicController(ModelController):
    """Test controller with public access."""

    model = ProjectModel
    schema_create = ProjectCreate
    schema_update = ProjectUpdate
    ownership_rule = OwnershipRule(
        claim_field="account_id",
        model_field="account_id",
        allow_public=True,
    )
