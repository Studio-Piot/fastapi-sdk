"""Pytest configuration file for the tests."""

from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from tests.app import app
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
