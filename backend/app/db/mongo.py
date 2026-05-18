from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from ..config import MONGO_URI

DATABASE_NAME: str = "memoryvault_db"
COLLECTION_NAME: str = "memories"
USERS_COLLECTION_NAME: str = "users"

_client: Optional[MongoClient] = None


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client


def _get_database() -> Database:
    return _get_client()[DATABASE_NAME]


# Expose the initialized client and default database for shared app-wide use.
mongo = _get_client()
db = _get_database()

try:
    setattr(mongo, "db", db)
except Exception:
    # Fallback for environments where the client object disallows custom attributes.
    pass


def get_memories_collection() -> Collection:
    return _get_database()[COLLECTION_NAME]


def get_users_collection() -> Collection:
    return _get_database()[USERS_COLLECTION_NAME]


def ping_mongo() -> bool:
    try:
        _get_client().admin.command("ping")
        return True
    except Exception:
        return False
