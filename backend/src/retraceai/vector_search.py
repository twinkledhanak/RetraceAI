import datetime
import logging

from bson import ObjectId
from bson.decimal128 import Decimal128
from pymongo.errors import OperationFailure

from retraceai.config import get_settings
from retraceai.db import get_database

logger = logging.getLogger("retraceai")


def make_json_safe(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(v) for v in value]
    return value


def search_upgrade_sessions(query: str, limit: int = 5) -> list[dict]:
    settings = get_settings()
    logger.info(
        "  Atlas: building $vectorSearch pipeline (index=%s, path=%s)",
        settings.vector_index_name,
        settings.vector_path,
    )
    pipeline = [
        {
            "$vectorSearch": {
                "index": settings.vector_index_name,
                "path": settings.vector_path,
                "query": query,
                "numCandidates": 200,
                "limit": limit,
            }
        },
        {"$addFields": {"score": {"$meta": "vectorSearchScore"}}},
    ]
    db = get_database()
    docs = db[settings.mongo_collection].aggregate(pipeline)
    results = [make_json_safe(doc) for doc in docs]
    logger.info("  Atlas: $vectorSearch returned %d document(s)", len(results))
    return results


def vector_search_error_message(exc: Exception) -> str:
    if isinstance(exc, OperationFailure):
        index = get_settings().vector_index_name
        return f"Atlas $vectorSearch failed (check that the '{index}' index exists): {exc.details}"
    return f"Atlas $vectorSearch failed: {exc}"
