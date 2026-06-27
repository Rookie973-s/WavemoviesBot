from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME, AUTO_DELETE_SECONDS

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        _db = _client[DB_NAME]
    return _db


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expires_at() -> datetime | None:
    """Return expiry datetime if auto-delete is enabled, else None."""
    if AUTO_DELETE_SECONDS and AUTO_DELETE_SECONDS > 0:
        from datetime import timedelta
        return _now() + timedelta(seconds=AUTO_DELETE_SECONDS)
    return None


# ─── File operations ──────────────────────────────────────────────────────────

async def save_file(file_key: str, file_data: dict):
    """Save a file entry. Adds created_at and optional expires_at."""
    db = get_db()
    file_data.setdefault("created_at", _now())
    exp = _expires_at()
    if exp:
        file_data["expires_at"] = exp
    await db.files.update_one(
        {"key": file_key},
        {"$set": file_data},
        upsert=True,
    )


async def get_file(file_key: str):
    """Retrieve a file entry by key. Returns None if expired."""
    db = get_db()
    record = await db.files.find_one({"key": file_key})
    if record and _is_expired(record):
        await db.files.delete_one({"key": file_key})
        return None
    return record


async def delete_file(file_key: str) -> bool:
    """Delete a single file entry. Returns True if something was deleted."""
    db = get_db()
    result = await db.files.delete_one({"key": file_key})
    return result.deleted_count > 0


async def count_files():
    db = get_db()
    return await db.files.count_documents({})


# ─── Batch operations ─────────────────────────────────────────────────────────

async def save_batch(batch_key: str, batch_data: dict):
    """
    Save a batch entry.
    batch_data = {
        "key": str,
        "title": str,
        "files": [ { file_key, file_type, original_name } ... ],
        "created_at": datetime,
        "expires_at": datetime | None,
    }
    """
    db = get_db()
    batch_data.setdefault("created_at", _now())
    exp = _expires_at()
    if exp:
        batch_data["expires_at"] = exp
    await db.batches.update_one(
        {"key": batch_key},
        {"$set": batch_data},
        upsert=True,
    )


async def get_batch(batch_key: str):
    """Retrieve a batch by key. Returns None if expired."""
    db = get_db()
    record = await db.batches.find_one({"key": batch_key})
    if record and _is_expired(record):
        await db.batches.delete_one({"key": batch_key})
        return None
    return record


async def delete_batch(batch_key: str) -> bool:
    """Delete a batch and all its constituent files."""
    db = get_db()
    batch = await db.batches.find_one({"key": batch_key})
    if batch:
        file_keys = [f["file_key"] for f in batch.get("files", [])]
        if file_keys:
            await db.files.delete_many({"key": {"$in": file_keys}})
    result = await db.batches.delete_one({"key": batch_key})
    return result.deleted_count > 0


async def list_batches(limit: int = 20):
    """Return the most recent batches (up to limit)."""
    db = get_db()
    cursor = db.batches.find({}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def count_batches():
    db = get_db()
    return await db.batches.count_documents({})


# ─── User operations ──────────────────────────────────────────────────────────

async def save_user(user_id: int, username: str = None, full_name: str = None):
    """Upsert a user record."""
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": {"username": username, "full_name": full_name},
            "$setOnInsert": {"user_id": user_id, "joined_at": _now()},
        },
        upsert=True,
    )


async def count_users():
    db = get_db()
    return await db.users.count_documents({})


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _is_expired(record: dict) -> bool:
    exp = record.get("expires_at")
    if not exp:
        return False
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return _now() > exp
