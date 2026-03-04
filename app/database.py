from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Connect to MongoDB on app startup."""
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.workouts.create_index([("user_id", 1), ("date", -1)])
    await db.meals.create_index([("user_id", 1), ("date", -1)])
    await db.exercises.create_index("name", unique=True)
    await db.ai_cache.create_index("query_hash")
    await db.ai_cache.create_index("created_at", expireAfterSeconds=86400)  # TTL 24h

    print("✅ Connected to MongoDB")


async def close_db():
    """Close MongoDB connection on app shutdown."""
    global client
    if client:
        client.close()
        print("🔌 Disconnected from MongoDB")


def get_db():
    """Get database instance."""
    return db
