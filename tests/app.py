"""FastAPI test application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_sdk.controllers import ModelController
from fastapi_sdk.middleware.auth import AuthMiddleware
from tests.config import settings
from tests.controllers import Account, Project, Task
from tests.routes import account_routes, project_routes, task_routes


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    """
    # Register controllers
    ModelController.register_controller("Account", Account)
    ModelController.register_controller("Project", Project)
    ModelController.register_controller("Task", Task)

    app.include_router(account_routes.router)
    app.include_router(project_routes.router)
    app.include_router(task_routes.router)

    yield


app = FastAPI(
    title="FastAPI test appication",
    summary="",
    lifespan=lifespan,
)

# Add auth middleware
app.add_middleware(
    AuthMiddleware,
    public_routes=settings.PUBLIC_ROUTES,  # Routes that don't require auth
    auth_issuer=settings.AUTH_ISSUER,  # Your authentication server URL
    auth_client_id=settings.FAUTHY_CLIENT_ID,  # Your client ID for authentication
    env=settings.ENVIRONMENT,  # Environment: "development" or "production"
    test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,  # Path to private key for development
    test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
)
