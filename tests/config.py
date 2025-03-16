"""App configuration"""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings"""

    MONGO_DATABASE_URI: str = os.environ["MONGO_DATABASE_URI"]
    MONGO_DATABASE_NAME: str = os.environ["MONGO_DATABASE_NAME"]


settings = Settings()
