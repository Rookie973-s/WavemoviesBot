from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        _db = _client[DB_NAME]
    return _db


# ─── File operations ──────────────────────────────────────────────────────────

async def save_file(file_key: str, file_data: dict):
    """Save a file entry. file_data includes file_id, file_type, caption."""
    db = get_db()
    await db.files.update_one(
        {"key": file_key},
        {"$set": file_data},
        upsert=True,
    )


async def get_file(file_key: str):
    """Retrieve a file entry by its key."""
    db = get_db()
    return await db.files.find_one({"key": file_key})


async def count_files():
    db = get_db()
    return await db.files.count_documents({})


# ─── User operations ──────────────────────────────────────────────────────────

async def save_user(user_id: int, username: str = None, full_name: str = None):
    """Upsert a user record."""
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "full_name": full_name}, "$setOnInsert": {"user_id": user_id}},
        upsert=True,
    )


async def count_users():
    db = get_db()
    return await db.users.count_documents({})
