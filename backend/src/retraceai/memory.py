"""Write layer: store new upgrade information in Atlas (RetraceAI's memory)."""

import logging

from retraceai.config import get_settings
from retraceai.db import get_database
from retraceai.vector_search import make_json_safe

logger = logging.getLogger("retraceai")


def add_attempt_to_session(session_id: str, attempt: dict) -> dict:
    settings = get_settings()
    logger.info("Step 1: Received attempt to append -> sessionId=%s", session_id)
    logger.info("Step 2: Invoking Atlas to modify document and add new information to memory")
    logger.info(
        "  Atlas: updating %s.%s ...",
        settings.mongo_db,
        settings.mongo_collection,
    )
    try:
        collection = get_database()[settings.mongo_collection]
        result = collection.update_one({"sessionId": session_id}, {"$push": {"attempts": attempt}})
    except Exception as exc:
        logger.error("Step 2: FAILED -> %s", exc)
        raise RuntimeError(f"Failed to update Atlas: {exc}") from exc

    if result.matched_count == 0:
        logger.error("Step 2: FAILED -> no session with sessionId=%r", session_id)
        raise KeyError(f"No session found with sessionId={session_id}")

    doc = collection.find_one({"sessionId": session_id})
    logger.info("Step 2: COMPLETE -> attempts now has %d row(s)", len(doc.get("attempts", [])))
    logger.info("Step 3: Returning updated document")
    return make_json_safe(doc)
