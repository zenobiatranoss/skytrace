from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_bounds, get_db
from app.providers.base import Bounds
from app.schemas.aircraft import AircraftDetail, AircraftPosition
from app.schemas.track import TrackOut
from app.services import aircraft_service, position_service, track_service

router = APIRouter(prefix="/aircraft", tags=["aircraft"])


@router.get("", response_model=list[AircraftPosition])
def list_aircraft(
    bounds: Bounds | None = Depends(get_bounds),
    limit: int | None = Query(None, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> list[AircraftPosition]:
    return position_service.list_positions(db, bounds=bounds, limit=limit)


@router.get("/{icao24}", response_model=AircraftDetail)
async def get_aircraft(icao24: str, db: Session = Depends(get_db)) -> AircraftDetail:
    return await aircraft_service.get_detail(db, icao24)


@router.get("/{icao24}/track", response_model=TrackOut)
def get_track(
    icao24: str,
    hours: int = Query(6, ge=1, le=72),
    db: Session = Depends(get_db),
) -> TrackOut:
    return track_service.get_track(db, icao24, hours=hours)
