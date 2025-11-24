"""App configuration"""

import json
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings"""

    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "test")
    MONGO_DATABASE_URI: str = os.environ.get(
        "MONGO_DATABASE_URI", "mongodb://localhost:27017"
    )
    MONGO_DATABASE_NAME: str = os.environ.get("MONGO_DATABASE_NAME", "test_fastapi_sdk")
    PUBLIC_ROUTES: list[str] = json.loads(os.environ.get("PUBLIC_ROUTES", "[]"))
    TEST_PRIVATE_KEY_PATH: str = os.environ.get(
        "TEST_PRIVATE_KEY_PATH", "test_private_key.pem"
    )
    TEST_PUBLIC_KEY_PATH: str = os.environ.get(
        "TEST_PUBLIC_KEY_PATH", "test_public_key.pem"
    )
    AUTH_ISSUER: str = os.environ.get("AUTH_ISSUER", "https://auth.fauthy.com")
    AUTH_CLIENT_ID: str = os.environ.get("AUTH_CLIENT_ID", "test_client_id")
    WEBHOOK_SECRET: str = os.environ.get("WEBHOOK_SECRET", "test_webhook_secret")
    WEBHOOK_MAX_AGE_SECONDS: int = 300


settings = Settings()
