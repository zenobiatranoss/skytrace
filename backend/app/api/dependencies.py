from fastapi import Query

from app.db.session import get_db
from app.providers.base import Bounds

__all__ = ["get_bounds", "get_db"]


def get_bounds(
    lamin: float | None = Query(None, ge=-90, le=90),
    lomin: float | None = Query(None, ge=-180, le=180),
    lamax: float | None = Query(None, ge=-90, le=90),
    lomax: float | None = Query(None, ge=-180, le=180),
) -> Bounds | None:
    """bounds are all-or-nothing. a partial box is treated as no box, so we
    never silently return a wrong slice."""
    values = (lamin, lomin, lamax, lomax)
    if any(v is None for v in values):
        return None
    return (lamin, lomin, lamax, lomax)  # type: ignore[return-value]
