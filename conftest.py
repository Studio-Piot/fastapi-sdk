"""Pytest configuration file for the tests."""

from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from fastapi_sdk.utils.test import create_access_token
from tests.app import app
from tests.config import settings
from tests.db import get_db_engine
from tests.models import AccountModel, ProjectModel, TaskModel


@pytest.fixture
def client() -> Generator:
    """Create a new TestClient instance for each test."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator:
    """Create a new MongoDB connection to be used as dependency."""
    db_client = AsyncIOMotorClient("mongodb://localhost:27017")
    _db_engine = AIOEngine(client=db_client, database="fastapi_sdk_test")

    try:
        yield _db_engine
    finally:
        db_client.close()


def override_get_db_engine():
    """
    This function is used to override the get_db function in the db.session module.
    """
    db_client = AsyncIOMotorClient("mongodb://localhost:27017")
    _db_engine = AIOEngine(client=db_client, database="fastapi_sdk_test")
    try:
        yield _db_engine
    finally:
        db_client.close()


app.dependency_overrides[get_db_engine] = override_get_db_engine


@pytest_asyncio.fixture(autouse=True)
async def clear_database(db_engine):
    """Clears the customer collection before each test."""
    await db_engine.remove(AccountModel, {})
    await db_engine.remove(ProjectModel, {})
    await db_engine.remove(TaskModel, {})


@pytest.fixture
def mock_jwt_token(account):
    """Generates a mock JWT token for testing."""
    return create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test_user",
            "account_id": account.uuid,
            "roles": ["admin"],
            "permissions": [
                "account:create",
                "account:read",
                "account:update",
                "account:delete",
                "project:create",
                "project:read",
                "project:update",
                "project:delete",
                "task:create",
                "task:read",
                "task:update",
                "task:delete",
            ],
        },
        expires_delta=timedelta(minutes=30),
    )


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Create headers with JWT token."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture
def mock_jwt_token_no_account_id():
    """Generates a mock JWT token for testing."""
    return create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test_user",
            "roles": ["admin"],
            "permissions": [
                "account:create",
                "account:read",
                "account:update",
                "account:delete",
                "project:create",
                "project:read",
                "project:update",
                "project:delete",
                "task:create",
                "task:read",
                "task:update",
                "task:delete",
            ],
        },
        expires_delta=timedelta(minutes=30),
    )


@pytest.fixture
def auth_headers_no_account_id(mock_jwt_token_no_account_id):
    """Create headers with JWT token."""
    return {"Authorization": f"Bearer {mock_jwt_token_no_account_id}"}


@pytest.fixture
def different_mock_jwt_token():
    """Generates a mock JWT token for testing."""
    return create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test_user",
            "account_id": "acc_456",
            "roles": ["admin"],
            "permissions": [
                "account:create",
                "account:read",
                "account:update",
                "account:delete",
                "project:create",
                "project:read",
                "project:update",
                "project:delete",
                "task:create",
                "task:read",
                "task:update",
                "task:delete",
            ],
        },
        expires_delta=timedelta(minutes=30),
    )


@pytest.fixture
def different_auth_headers(different_mock_jwt_token):
    """Create headers with JWT token."""
    return {"Authorization": f"Bearer {different_mock_jwt_token}"}


@pytest_asyncio.fixture
async def account(db_engine):
    """Create a test account."""
    _account = AccountModel(
        name="TestAccount",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await db_engine.save(_account)
    yield _account
    await db_engine.delete(_account)


@pytest_asyncio.fixture
async def deleted_account(db_engine):
    """Create a deleted test account."""
    _account = AccountModel(
        name="Deleted Account",
        deleted=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await db_engine.save(_account)
    yield _account
    await db_engine.delete(_account)


@pytest_asyncio.fixture
async def project(db_engine, account):
    """Create a test project."""
    project = ProjectModel(
        name="Test Project",
        description="Test Description",
        account_id=account.uuid,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await db_engine.save(project)
    yield project
    await db_engine.delete(project)


@pytest_asyncio.fixture
async def deleted_project(db_engine, account):
    """Create a deleted test project."""
    project = ProjectModel(
        name="Deleted Project",
        description="Deleted Description",
        account_id=account.uuid,
        deleted=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await db_engine.save(project)
    yield project
    await db_engine.delete(project)


@pytest_asyncio.fixture
async def task(db_engine, project, account):
    """Create a test task."""
    task = TaskModel(
        title="Test Task",
        description="Test Description",
        project_id=project.uuid,
        account_id=account.uuid,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await db_engine.save(task)
    yield task
    await db_engine.delete(task)


@pytest_asyncio.fixture
async def deleted_task(db_engine, project, account):
    """Create a deleted test task."""
    task = TaskModel(
        title="Deleted Task",
        description="Deleted Description",
        project_id=project.uuid,
        account_id=account.uuid,
        deleted=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await db_engine.save(task)
    yield task
    await db_engine.delete(task)
