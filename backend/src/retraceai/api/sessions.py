import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from retraceai.config import get_settings
from retraceai.db import get_database
from retraceai.memory import add_attempt_to_session
from retraceai.vector_search import make_json_safe

logger = logging.getLogger("retraceai")

router = APIRouter(tags=["sessions"])


class AppVersion(BaseModel):
    from_: str = Field(..., alias="from")
    to: str


class Attempt(BaseModel):
    library: str
    action: str
    fromVersion: str | None = None
    toVersion: str | None = None
    succeeded: bool
    errorText: str | None = None
    notes: str | None = None


class SessionDocument(BaseModel):
    sessionId: str
    appVersion: AppVersion
    status: str
    attempts: list[Attempt]
    coupledWith: list[str] = Field(default_factory=list)
    timestamp: str | None = None


@router.post("/sessions", status_code=201)
def create_session(doc: SessionDocument) -> dict:
    settings = get_settings()
    logger.info("Step 1: Session payload received -> sessionId=%s", doc.sessionId)

    payload = doc.model_dump(by_alias=True)
    if not payload.get("timestamp"):
        payload["timestamp"] = datetime.now(UTC).isoformat()

    logger.info(
        "Step 2: Writing document to Atlas %s.%s ...",
        settings.mongo_db,
        settings.mongo_collection,
    )
    try:
        collection = get_database()[settings.mongo_collection]
        result = collection.insert_one(payload)
    except Exception as exc:
        logger.error("Step 2: FAILED -> %s", exc)
        raise HTTPException(status_code=503, detail=f"Failed to write to Atlas: {exc}") from exc

    created = collection.find_one({"_id": result.inserted_id})
    logger.info("Step 2: COMPLETE -> inserted _id=%s", result.inserted_id)
    logger.info("Step 3: Returning created document to client")
    return make_json_safe(created)


@router.post("/sessions/{session_id}/attempts", status_code=200)
def add_attempt(session_id: str, attempt: Attempt) -> dict:
    try:
        return add_attempt_to_session(session_id, attempt.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
