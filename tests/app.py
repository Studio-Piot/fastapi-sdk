"""FastAPI test application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_sdk.controllers import ModelController
from fastapi_sdk.middleware.auth import AuthMiddleware
from fastapi_sdk.security.webhook import verify_revolut_signature
from fastapi_sdk.utils.exception_handler import register_exception_handlers
from fastapi_sdk.webhook.handler import registry
from fastapi_sdk.webhook.route import create_webhook_router
from tests.config import settings
from tests.controllers import Account, Project, Task
from tests.routes import account_routes, project_routes, task_routes


@registry.register("account.created")
async def handle_account_created(payload: dict):
    """Handle the account.created event"""
    account_data = payload.get("data")
    return {
        "status": "ok",
        "result": f"Account created with data {account_data['name']}",
    }


webhook_router = create_webhook_router(
    webhook_secret=settings.WEBHOOK_SECRET,
    max_age_seconds=settings.WEBHOOK_MAX_AGE_SECONDS,
    prefix="/webhook",
    tags=["Webhook"],
)


@registry.register("ORDER_COMPLETED")
async def handle_order_completed(payload: dict):
    """Handle the order.completed event"""
    return {
        "status": "ok",
        "result": f"Order completed with data {payload['order_id']}",
    }


# Create webhook router with custom header names (like Revolut)
revolut_webhook_router = create_webhook_router(
    webhook_secret=settings.WEBHOOK_SECRET,
    max_age_seconds=settings.WEBHOOK_MAX_AGE_SECONDS,
    prefix="/revolut-webhook",
    signature_header="Revolut-Signature",
    timestamp_header="Revolut-Request-Timestamp",
    signature_verifier=verify_revolut_signature,
    tags=["revolut-webhooks"],
)


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
    app.include_router(webhook_router)
    app.include_router(revolut_webhook_router)

    yield


app = FastAPI(
    title="FastAPI test appication",
    summary="",
    lifespan=lifespan,
)

# Register exception handlers for standardized response format
register_exception_handlers(app)

# Add auth middleware
app.add_middleware(
    AuthMiddleware,
    public_routes=settings.PUBLIC_ROUTES,  # Routes that don't require auth
    auth_issuer=settings.AUTH_ISSUER,  # Your authentication server URL
    auth_client_id=settings.AUTH_CLIENT_ID,  # Your client ID for authentication
    env=settings.ENVIRONMENT,  # Environment: "development" or "production"
    jwk_url=settings.JWK_URL,  # URL to fetch JWK from
    test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,  # Path to private key for development
    test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
)
