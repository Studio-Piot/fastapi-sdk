"""Create a database instance to be used as a dependency."""

from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from tests.config import settings


async def get_db_engine():
    """Create a new MongoDB connection to be used as dependency."""
    client = AsyncIOMotorClient(settings.MONGO_DATABASE_URI)
    db_engine = AIOEngine(client=client, database=settings.MONGO_DATABASE_NAME)
    try:
        yield db_engine
    finally:
        client.close()
