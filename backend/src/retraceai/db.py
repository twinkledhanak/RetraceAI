from functools import lru_cache

from pymongo import MongoClient

from retraceai.config import get_settings


@lru_cache
def get_db_client() -> MongoClient | None:
    settings = get_settings()
    if not settings.mongodb_uri:
        return None
    return MongoClient(settings.mongodb_uri.get_secret_value())


def get_database():
    client = get_db_client()
    if client is None:
        raise RuntimeError("MONGODB_URI not configured")
    return client[get_settings().mongo_db]
