import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from retraceai.config import get_settings
from retraceai.gemini import needs_vector_search
from retraceai.vector_search import search_upgrade_sessions, vector_search_error_message

logger = logging.getLogger("retraceai")

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class SearchResult(BaseModel):
    score: float = 0.0
    document: dict


class SearchResponse(BaseModel):
    query: str
    needs_vector_search: bool
    decision_reason: str | None = None
    results: list[SearchResult]


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    settings = get_settings()
    logger.info("Step 1: Query received -> %r", request.query)

    logger.info("Step 2: Connecting to Gemini to decide if vector search is needed...")
    decision, reason = needs_vector_search(request.query)
    logger.info("Step 2: COMPLETE -> needs_vector_search=%s (%s)", decision, reason)

    results: list[SearchResult] = []
    if decision:
        logger.info(
            "Step 3: Connecting to Atlas -> running $vectorSearch on %s.%s ...",
            settings.mongo_db,
            settings.mongo_collection,
        )
        try:
            docs = search_upgrade_sessions(request.query)
        except Exception as exc:
            logger.error("Step 3: FAILED -> %s", exc)
            raise HTTPException(status_code=503, detail=vector_search_error_message(exc)) from exc
        logger.info("Step 3: COMPLETE -> %d matching document(s)", len(docs))
        results = [
            SearchResult(score=d["score"], document=d) for d in docs
        ]
    else:
        logger.info("Step 3: SKIPPED -> Gemini decided vector search is not needed")

    logger.info("Step 4: Returning response to client")
    return SearchResponse(
        query=request.query,
        needs_vector_search=decision,
        decision_reason=reason,
        results=results,
    )
