from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class SearchResult(BaseModel):
    title: str
    snippet: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    return SearchResponse(
        query=request.query,
        results=[
            SearchResult(
                title="(placeholder search results)",
                snippet="Dummy output — real vector search will be plugged in here.",
            )
        ],
    )
