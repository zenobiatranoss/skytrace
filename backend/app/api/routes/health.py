from fastapi import APIRouter

from app.cache.aircraft_cache import aircraft_cache
from app.services.data_refresh_service import refresh_loop
from app.utils.time import age_seconds

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    updated = aircraft_cache.updated_at
    return {
        "status": "ok",
        "aircraft_tracked": aircraft_cache.size(),
        "last_update": updated.isoformat() if updated else None,
        "last_update_age_seconds": age_seconds(updated),
        "refresh_interval_seconds": refresh_loop.interval,
        "last_error": refresh_loop.last_error,
    }
