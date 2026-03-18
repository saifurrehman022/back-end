from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)

async def get_db() -> AsyncIOMotorDatabase:
    return client[settings.database_name]