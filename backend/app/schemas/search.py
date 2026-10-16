from pydantic import BaseModel


class SearchResult(BaseModel):
    kind: str  # aircraft | airport | flight
    id: str
    label: str
    subtitle: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult] = []
