"""FastAPI test application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_sdk.controllers import ModelController
from tests.controllers import Account, Project, Task


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    """
    # Register controllers
    ModelController.register_controller("Account", Account)
    ModelController.register_controller("Project", Project)
    ModelController.register_controller("Task", Task)

    yield


app = FastAPI(
    title="FastAPI test appication",
    summary="",
    lifespan=lifespan,
)
