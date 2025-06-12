"""App configuration"""

import json
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings"""

    ENVIRONMENT: str = os.environ["ENVIRONMENT"]
    MONGO_DATABASE_URI: str = os.environ["MONGO_DATABASE_URI"]
    MONGO_DATABASE_NAME: str = os.environ["MONGO_DATABASE_NAME"]
    PUBLIC_ROUTES: list[str] = json.loads(os.environ["PUBLIC_ROUTES"])
    TEST_PRIVATE_KEY_PATH: str = os.environ["TEST_PRIVATE_KEY_PATH"]
    TEST_PUBLIC_KEY_PATH: str = os.environ["TEST_PUBLIC_KEY_PATH"]
    AUTH_ISSUER: str = os.environ["AUTH_ISSUER"]
    AUTH_CLIENT_ID: str = os.environ["AUTH_CLIENT_ID"]
    WEBHOOK_SECRET: str = os.environ["WEBHOOK_SECRET"]
    WEBHOOK_MAX_AGE_SECONDS: int = 300


settings = Settings()
