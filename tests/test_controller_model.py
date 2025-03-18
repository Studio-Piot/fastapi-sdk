"""Test controller."""

import time
from datetime import UTC

import pytest
from motor.core import AgnosticDatabase

from fastapi_sdk.controllers import ModelController
from tests.controllers import Account, Project, Task


@pytest.fixture(autouse=True)
def register_controllers():
    """Register controllers for testing."""
    ModelController.register_controller("Account", Account)
    ModelController.register_controller("Project", Project)
    ModelController.register_controller("Task", Task)


async def fixtures(db_engine: AgnosticDatabase):
    """Re-usable test fictures"""
    account_1 = await Account(db_engine).create({"name": "Account 1"})
    account_2 = await Account(db_engine).create({"name": "Account 2"})

    return account_1, account_2


@pytest.mark.asyncio
async def test_model_controller(db_engine: AgnosticDatabase):
    """Test model controller."""

    # Create two accounts, one for crud test and one for listing
    account_1, account_2 = await fixtures(db_engine)

    assert account_1.uuid
    assert account_1.name == "Account 1"
    assert account_1.created_at
    assert account_1.updated_at

    # Get account
    account_1 = await Account(db_engine).get(uuid=account_1.uuid)
    assert account_1

    # Sleep for 1 seconds to test updated_at
    time.sleep(1)

    # Update account
    account_1 = await Account(db_engine).update(
        uuid=account_1.uuid, data={"name": "Account 1 Updated"}
    )

    assert account_1.name == "Account 1 Updated"
    assert account_1.updated_at > account_1.created_at.replace(tzinfo=UTC)

    # List accounts
    accounts = await Account(db_engine).list()
    assert len(accounts["items"]) == 2
    assert accounts["total"] == 2
    assert accounts["page"] == 0
    assert accounts["pages"] == 1

    # Delete account
    account_1 = await Account(db_engine).delete(uuid=account_1.uuid)
    assert account_1.deleted is True

    # Get deleted account
    deleted_account = await Account(db_engine).get(uuid=account_1.uuid)
    assert deleted_account is None

    # Update deleted account
    deleted_account = await Account(db_engine).update(
        uuid=account_1.uuid, data={"name": "Account 1 Updated"}
    )
    assert deleted_account is None

    # List accounts with one deleted
    accounts = await Account(db_engine).list()
    assert len(accounts["items"]) == 1
    assert accounts["items"][0].uuid == account_2.uuid
    assert accounts["total"] == 1
    assert accounts["page"] == 0
    assert accounts["pages"] == 1


@pytest.mark.asyncio
async def test_list_options(db_engine: AgnosticDatabase):
    """Test the list options of the controller."""

    # Create two accounts, one for crud test and one for listing
    account_1, account_2 = await fixtures(db_engine)

    # Default listing
    accounts = await Account(db_engine).list()
    assert len(accounts["items"]) == 2
    assert accounts["total"] == 2
    assert accounts["page"] == 0
    assert accounts["pages"] == 1

    # List with page 2 (Page 1 is the same as default, page 0)
    accounts = await Account(db_engine).list(page=2)
    assert len(accounts["items"]) == 0
    assert accounts["total"] == 2
    assert accounts["page"] == 2
    assert accounts["pages"] == 1

    # List with query
    accounts = await Account(db_engine).list(query=[{"name": "Account 1"}])
    assert len(accounts["items"]) == 1
    assert accounts["items"][0].uuid == account_1.uuid
    assert accounts["total"] == 1
    assert accounts["page"] == 0
    assert accounts["pages"] == 1

    # List with order_by
    accounts = await Account(db_engine).list(order_by={"name": -1})
    assert len(accounts["items"]) == 2
    assert accounts["items"][0].uuid == account_2.uuid
    assert accounts["items"][1].uuid == account_1.uuid
    assert accounts["total"] == 2
    assert accounts["page"] == 0
    assert accounts["pages"] == 1


@pytest.mark.asyncio
async def test_relationships(db_engine: AgnosticDatabase):
    """Test relationship handling between models."""
    # Create an account
    account = await Account(db_engine).create({"name": "Test Account"})

    # Create a project for this account
    project = await Project(db_engine).create(
        {"name": "Test Project", "account_id": account.uuid}
    )

    # Create a task for this project
    task = await Task(db_engine).create(
        {
            "description": "Test Task",
            "account_id": account.uuid,
            "project_id": project.uuid,
        }
    )

    # Test getting account with related projects
    account_with_projects = await Account(db_engine).get_with_relations(
        uuid=account.uuid, include=["projects"]
    )
    assert len(account_with_projects.projects) == 1
    assert account_with_projects.projects[0].uuid == project.uuid

    # Test getting project with related account and tasks
    project_with_relations = await Project(db_engine).get_with_relations(
        uuid=project.uuid, include=["account", "tasks"]
    )
    assert project_with_relations.account.uuid == account.uuid
    assert len(project_with_relations.tasks) == 1
    assert project_with_relations.tasks[0].uuid == task.uuid

    # Test cascade delete
    await Account(db_engine).delete_with_relations(uuid=account.uuid)

    # Verify everything is deleted
    deleted_project = await Project(db_engine).get(uuid=project.uuid)
    deleted_task = await Task(db_engine).get(uuid=task.uuid)
    assert deleted_project is None
    assert deleted_task is None
